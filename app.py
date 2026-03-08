import os, threading, time, io, random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from flask import Flask, Response, render_template, request, jsonify
import pygame
import neat

app = Flask(__name__)

# ── shared state ──
current_mode  = None
game_thread   = None
running       = False
frame_lock    = threading.Lock()
latest_frame  = None
player_action = None

pygame.init()
WIN_W, WIN_H = 500, 800

# ── load images once ──
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png"))),
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
BG_IMG   = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT  = pygame.font.SysFont("comicsans", 70)


# ════════════════════════════════════════
#  GAME CLASSES
# ════════════════════════════════════════

class Bird:
    MAX_ROTATION = 25; ROT_VEL = 20; ANIMATION_TIME = 5
    def __init__(self, x, y):
        self.x=x; self.y=y; self.tilt=0; self.tick_count=0
        self.vel=0; self.height=y; self.img_count=0; self.img=BIRD_IMGS[0]
    def jump(self): self.vel=-10.5; self.tick_count=0; self.height=self.y
    def move(self):
        self.tick_count+=1
        d=self.vel*self.tick_count+1.5*self.tick_count**2
        if d>=16: d=16
        if d<0: d-=2
        self.y+=d
        if d<0 or self.y<self.height+50:
            if self.tilt<self.MAX_ROTATION: self.tilt=self.MAX_ROTATION
        else:
            if self.tilt>-90: self.tilt-=self.ROT_VEL
    def draw(self, win):
        self.img_count+=1; t=self.ANIMATION_TIME
        if   self.img_count<t:      self.img=BIRD_IMGS[0]
        elif self.img_count<t*2:    self.img=BIRD_IMGS[1]
        elif self.img_count<t*3:    self.img=BIRD_IMGS[2]
        elif self.img_count<t*4:    self.img=BIRD_IMGS[1]
        elif self.img_count==t*4+1: self.img=BIRD_IMGS[0]; self.img_count=0
        if self.tilt<=-80: self.img=BIRD_IMGS[1]; self.img_count=t*2
        rot=pygame.transform.rotate(self.img,self.tilt)
        rect=rot.get_rect(center=self.img.get_rect(topleft=(self.x,self.y)).center)
        win.blit(rot,rect.topleft)
    def get_mask(self): return pygame.mask.from_surface(self.img)

class Pipe:
    GAP=200; VEL=5
    def __init__(self, x):
        self.x=x; self.height=0; self.top=0; self.bottom=0
        self.PIPE_TOP=pygame.transform.flip(PIPE_IMG,False,True)
        self.PIPE_BOTTOM=PIPE_IMG; self.passed=False; self.set_height()
    def set_height(self):
        self.height=random.randrange(50,450)
        self.top=self.height-self.PIPE_TOP.get_height()
        self.bottom=self.height+self.GAP
    def move(self): self.x-=self.VEL
    def draw(self, win):
        win.blit(self.PIPE_TOP,(self.x,self.top))
        win.blit(self.PIPE_BOTTOM,(self.x,self.bottom))
    def collide(self, bird):
        bm=bird.get_mask()
        tm=pygame.mask.from_surface(self.PIPE_TOP)
        bom=pygame.mask.from_surface(self.PIPE_BOTTOM)
        to=(self.x-bird.x,self.top-round(bird.y))
        bo=(self.x-bird.x,self.bottom-round(bird.y))
        return bool(bm.overlap(tm,to) or bm.overlap(bom,bo))

class Base:
    VEL=5
    def __init__(self, y):
        self.y=y; self.WIDTH=BASE_IMG.get_width(); self.x1=0; self.x2=self.WIDTH
    def move(self):
        self.x1-=self.VEL; self.x2-=self.VEL
        if self.x1+self.WIDTH<0: self.x1=self.x2+self.WIDTH
        if self.x2+self.WIDTH<0: self.x2=self.x1+self.WIDTH
    def draw(self, win):
        win.blit(BASE_IMG,(self.x1,self.y)); win.blit(BASE_IMG,(self.x2,self.y))


# ════════════════════════════════════════
#  CAPTURE FRAME
# ════════════════════════════════════════

def capture(win):
    global latest_frame
    buf=io.BytesIO()
    pygame.image.save(win, buf, "JPEG")
    with frame_lock:
        latest_frame=buf.getvalue()


# ════════════════════════════════════════
#  PLAYER THREAD
# ════════════════════════════════════════

def run_player():
    global running, player_action
    win=pygame.Surface((WIN_W,WIN_H)); clock=pygame.time.Clock()
    while running:
        bird=Bird(230,350); base=Base(730)
        pipes=[Pipe(600)]; score=0; game_over=False
        while running:
            clock.tick(30)
            if game_over:
                win.blit(BG_IMG,(0,0))
                ov=pygame.Surface((WIN_W,WIN_H),pygame.SRCALPHA); ov.fill((0,0,0,150))
                win.blit(ov,(0,0))
                go=END_FONT.render("Game Over",1,(255,80,80))
                win.blit(go,(WIN_W//2-go.get_width()//2,250))
                sc=STAT_FONT.render("Score: "+str(score),1,(255,255,255))
                win.blit(sc,(WIN_W//2-sc.get_width()//2,340))
                btn=pygame.Rect(WIN_W//2-110,440,220,65)
                pygame.draw.rect(win,(255,200,0),btn,border_radius=12)
                pygame.draw.rect(win,(200,140,0),btn,3,border_radius=12)
                bt=STAT_FONT.render("Try Again",1,(50,30,0))
                win.blit(bt,(btn.x+btn.width//2-bt.get_width()//2,
                             btn.y+btn.height//2-bt.get_height()//2))
                capture(win)
                action=player_action; player_action=None
                if action=='jump': break
                continue
            action=player_action; player_action=None
            if action=='jump': bird.jump()
            bird.move()
            add_pipe=False; rem=[]
            for pipe in pipes:
                pipe.move()
                if pipe.collide(bird): game_over=True
                if not pipe.passed and pipe.x<bird.x: pipe.passed=True; add_pipe=True
                if pipe.x+pipe.PIPE_TOP.get_width()<0: rem.append(pipe)
            if add_pipe: score+=1; pipes.append(Pipe(600))
            for r in rem: pipes.remove(r)
            if bird.y+bird.img.get_height()>=730 or bird.y<0: game_over=True
            base.move()
            win.blit(BG_IMG,(0,0))
            for pipe in pipes: pipe.draw(win)
            base.draw(win); bird.draw(win)
            t=STAT_FONT.render("Score: "+str(score),1,(255,255,255))
            win.blit(t,(WIN_W-10-t.get_width(),10))
            capture(win)


# ════════════════════════════════════════
#  AI THREAD
# ════════════════════════════════════════

GEN=0

def run_ai(show_rays):
    global running, GEN
    win=pygame.Surface((WIN_W,WIN_H)); clock=pygame.time.Clock(); GEN=0
    local_dir=os.path.dirname(os.path.abspath(__file__))
    config_path=os.path.join(local_dir,"config-feedforward.txt")
    config=neat.config.Config(
        neat.DefaultGenome,neat.DefaultReproduction,
        neat.DefaultSpeciesSet,neat.DefaultStagnation,config_path)

    def eval_genomes(genomes,config):
        global GEN; GEN+=1
        nets=[]; ge=[]; birds=[]
        for _,g in genomes:
            nets.append(neat.nn.FeedForwardNetwork.create(g,config))
            birds.append(Bird(230,350)); g.fitness=0; ge.append(g)
        base=Base(730); pipes=[Pipe(600)]; score=0
        while running and len(birds)>0:
            clock.tick(30)
            pipe_ind=0
            if len(pipes)>1 and birds[0].x>pipes[0].x+pipes[0].PIPE_TOP.get_width():
                pipe_ind=1
            for x,bird in enumerate(birds):
                bird.move(); ge[x].fitness+=0.1
                out=nets[x].activate((bird.y,
                    abs(bird.y-pipes[pipe_ind].height),
                    abs(bird.y-pipes[pipe_ind].bottom)))
                if out[0]>0.5: bird.jump()
            add_pipe=False; rem=[]
            for pipe in pipes:
                pipe.move()
                for x,bird in enumerate(birds):
                    if pipe.collide(bird):
                        ge[x].fitness-=1; birds.pop(x); nets.pop(x); ge.pop(x)
                    if not pipe.passed and pipe.x<bird.x:
                        pipe.passed=True; add_pipe=True
                if pipe.x+pipe.PIPE_TOP.get_width()<0: rem.append(pipe)
            if add_pipe:
                score+=1
                for g in ge: g.fitness+=5
                pipes.append(Pipe(600))
            for r in rem: pipes.remove(r)
            for x,bird in enumerate(birds):
                if bird.y+bird.img.get_height()>=730 or bird.y<0:
                    birds.pop(x); nets.pop(x); ge.pop(x)
            base.move()
            win.blit(BG_IMG,(0,0))
            for pipe in pipes: pipe.draw(win)
            base.draw(win)
            for bird in birds:
                bird.draw(win)
                if show_rays and len(pipes)>pipe_ind:
                    p=pipes[pipe_ind]
                    bx=bird.x+bird.img.get_width()/2
                    by=bird.y+bird.img.get_height()/2
                    pcx=p.x+p.PIPE_TOP.get_width()/2
                    for tx,ty in [(pcx,p.height),(pcx,p.bottom),
                                  (p.x,p.height),(p.x,p.bottom),
                                  (p.x+p.PIPE_TOP.get_width(),p.height),
                                  (p.x+p.PIPE_TOP.get_width(),p.bottom)]:
                        pygame.draw.line(win,(255,0,0),(bx,by),(tx,ty),2)
            t=STAT_FONT.render("Score: "+str(score),1,(255,255,255))
            win.blit(t,(WIN_W-10-t.get_width(),10))
            win.blit(STAT_FONT.render("Gen: "+str(GEN),1,(255,255,255)),(10,10))
            win.blit(STAT_FONT.render("Alive: "+str(len(birds)),1,(255,255,255)),(10,60))
            capture(win)

    p=neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())
    while running:
        p.run(eval_genomes,1)


# ════════════════════════════════════════
#  FLASK ROUTES
# ════════════════════════════════════════

def generate_frames():
    while True:
        with frame_lock:
            frame=latest_frame
        if frame:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')
        time.sleep(1/30)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/start/<mode>')
def start_mode(mode):
    global game_thread,running,current_mode,latest_frame
    running=False
    if game_thread and game_thread.is_alive(): game_thread.join(timeout=2)
    latest_frame=None; current_mode=mode; running=True
    if   mode=='player':    game_thread=threading.Thread(target=run_player,daemon=True)
    elif mode=='ai-vision': game_thread=threading.Thread(target=lambda:run_ai(True),daemon=True)
    elif mode=='ai-clean':  game_thread=threading.Thread(target=lambda:run_ai(False),daemon=True)
    game_thread.start()
    return jsonify({'status':'ok','mode':mode})

@app.route('/stop')
def stop_mode():
    global running,current_mode
    running=False; current_mode=None
    return jsonify({'status':'stopped'})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/action',methods=['POST'])
def action():
    global player_action
    data=request.get_json()
    if data and data.get('action')=='jump': player_action='jump'
    return jsonify({'status':'ok'})

if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0',port=port,threaded=True)
