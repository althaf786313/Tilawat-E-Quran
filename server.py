#!/usr/bin/env python3
"""Local streaming player for the user's J2ME game. Python 3 + a Java runtime."""
import os, sys, json, struct, subprocess, threading, time, shutil
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WIDTH,HEIGHT=220,176
JAVA=os.environ.get('JAVA_BIN') or shutil.which('java') or str(ROOT/'.runtime/jdk4py/java-runtime/bin/java')
EMU=ROOT/'vendor/freej2me-plus.jar'; GAME=ROOT/'vendor/johnny-crash.jar'
class Session:
 def __init__(self):
  self.proc=None; self.lock=threading.RLock(); self.error=None
 def send(self, kind, value=0, data=b''):
  self.proc.stdin.write(bytes([kind])+struct.pack('>I',value)+data); self.proc.stdin.flush()
 def read_exact(self,n):
  data=bytearray()
  while len(data)<n:
   chunk=self.proc.stdout.read(n-len(data))
   if not chunk: raise RuntimeError('Emulator stopped unexpectedly.')
   data.extend(chunk)
  return bytes(data)
 def start(self):
  with self.lock:
   self.stop()
   if not Path(JAVA).exists(): raise RuntimeError('Java runtime not found. Run the setup instructions in README.md.')
   self.proc=subprocess.Popen([JAVA,'-Djava.awt.headless=true','-Dfile.encoding=ISO_8859_1','-cp',str(EMU),'org.recompile.freej2me.Libretro',str(WIDTH),str(HEIGHT)],cwd=str(ROOT),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
   ready=self.proc.stdout.readline()
   if ready!=b'+READY\n': raise RuntimeError('Emulator failed to start.')
   path=str(GAME).encode();self.send(10,len(path),path);self.send(13,1,b'0')
 def frame(self):
  with self.lock:
   if not self.proc or self.proc.poll() is not None: raise RuntimeError('Game is not running. Press Start game.')
   self.send(15);header=self.read_exact(16)
   if header[0]!=254: raise RuntimeError('Unexpected emulator response.')
   w=header[1]*256+header[2];h=header[3]*256+header[4]
   if not w or not h: raise RuntimeError('The game requested an emulator restart. Please restart the game.')
   return header+self.read_exact(w*h*3)
 def key(self,key,down):
  with self.lock:
   if self.proc and self.proc.poll() is None:self.send(3 if down else 2,key)
 def stop(self):
  if self.proc:
   self.proc.kill()
   try:self.proc.wait(timeout=2)
   except subprocess.TimeoutExpired:pass
   self.proc=None
session=Session()
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def reply(self,status,obj):
  b=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_POST(self):
  try:
   if self.path=='/api/start':session.start();self.reply(200,{'ok':True})
   elif self.path=='/api/key':
    length=int(self.headers.get('Content-Length','0'))
    if length>1024:raise ValueError('Invalid request')
    data=json.loads(self.rfile.read(length)); key=int(data['key']);down=data['down']
    if not 0<=key<=19 or not isinstance(down,bool):raise ValueError('Invalid key')
    session.key(key,down);self.reply(200,{'ok':True})
   else:self.reply(404,{'error':'Not found'})
  except Exception as e:self.reply(500,{'error':str(e)})
 def do_GET(self):
  if self.path=='/api/frame':
   try:
    b=session.frame();self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
   except Exception as e:self.reply(500,{'error':str(e)})
  elif self.path.startswith('/vendor/') or self.path.startswith('/.runtime/') or self.path.startswith('/config/') or self.path.startswith('/freej2me_system/'):
   self.send_error(404)
  else:super().do_GET()
if __name__=='__main__':
 os.chdir(ROOT);port=int(os.environ.get('PORT','8001'))
 print(f'Johnny Crash player listening on 0.0.0.0:{port}',flush=True)
 try:ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
 finally:session.stop()
