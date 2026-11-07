#!/usr/bin/env python3
"""Per-game installer for the upstream MFG Unlocker; no system-wide injection."""
import hashlib, json, os, re, shutil, subprocess, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

ROOT = Path(__file__).resolve().parent
DLL = ROOT / 'MFGUnlocker.dll'
DLL_HASH = 'e6b6e6b70a6ed3af839c9647a32fc22660ae6b2d655062c5c072246c91fc10c7'
STATE = Path.home() / '.local/share/framegen-manager/installs.json'
PROXIES = ('version.dll','winmm.dll','xinput9_1_0.dll','dxgi.dll','d3d12.dll','dinput8.dll','dsound.dll')

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()

def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(value,indent=2)+'\n')
    os.replace(tmp,path)

def running(exe):
    target=str(exe).lower().replace('/','\\')
    name=exe.name.lower()
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            data=proc.read_bytes().replace(b'\0',b' ').decode(errors='ignore').lower().replace('/','\\')
            if name in data and (target in data or re.search(r'(?:\\|\s)'+re.escape(name)+r'(?:\s|$)',data)):
                return True
        except (OSError,PermissionError): pass
    return False

def config_dir(exe): return exe.parent

def steam_games():
    base=Path.home()/'.local/share/Steam/steamapps'
    libs={base}
    vf=base/'libraryfolders.vdf'
    if vf.exists():
        for x in re.findall(r'"path"\s+"([^"]+)"',vf.read_text(errors='replace')):
            libs.add(Path(x.replace('\\\\','\\'))/'steamapps')
    result=[]
    for lib in libs:
        for manifest in lib.glob('appmanifest_*.acf'):
            s=manifest.read_text(errors='replace')
            def val(k):
                m=re.search(r'"'+k+r'"\s+"([^"]+)"',s,re.I); return m.group(1) if m else ''
            appid,name,folder=val('appid'),val('name'),val('installdir')
            if appid and folder and (lib/'common'/folder).is_dir(): result.append((name,appid,lib/'common'/folder))
    return sorted(result,key=lambda x:x[0].casefold())

def launch_options(proxy, old):
    old=old.strip() or '%command%'
    if '%command%' not in old: raise ValueError('Existing launch options must contain %command%.')
    if re.search(r'(?i)\b(?:WINEDLLOVERRIDES|PROTON_NVIDIA_NVCUDA)\s*=',old):
        raise ValueError('Existing launch options already contain a DLL override or CUDA option. Merge them manually instead of replacing them.')
    return f'PROTON_NVIDIA_NVCUDA=1 WINEDLLOVERRIDES="{Path(proxy).stem}=n,b" {old}'

def install(exe, proxy, multiplier):
    if not exe.is_file() or exe.suffix.lower()!='.exe': raise ValueError('Choose the actual Windows game .exe.')
    if proxy not in PROXIES: raise ValueError('Unsupported loader name.')
    if running(exe): raise ValueError('Close the game before installing or changing its files.')
    if sha(DLL)!=DLL_HASH: raise ValueError('The bundled mod failed its integrity check.')
    target=exe.parent/proxy; cfg=exe.parent/'RTXMFG-Universal.json'
    state=load_state(); key=str(exe.resolve()); rec=state.get(key)
    if rec:
        if rec['proxy'] != str(target) or not target.exists() or sha(target)!=DLL_HASH:
            raise ValueError('The existing managed installation has changed. Inspect it before continuing.')
        current=json.loads(cfg.read_text()) if cfg.exists() else {}
        current.update(followGame=False,mode='fixed',multiplier=int(multiplier))
        atomic_json(cfg,current); rec['config_hash']=sha(cfg); atomic_json(STATE,state); return
    if target.exists(): raise ValueError(f'{proxy} already exists. Choose another name; it will not be overwritten.')
    if cfg.exists(): raise ValueError('An MFG Unlocker configuration already exists here. This app will not overwrite or adopt it.')
    shutil.copyfile(DLL,target)
    try:
        atomic_json(cfg,{'followGame':False,'mode':'fixed','multiplier':int(multiplier)})
        state[key]={'proxy':str(target),'config':str(cfg),'config_hash':sha(cfg)}
        atomic_json(STATE,state)
    except Exception:
        target.unlink(missing_ok=True); cfg.unlink(missing_ok=True); raise

def remove(exe):
    if running(exe): raise ValueError('Close the game before removing the mod.')
    state=load_state();key=str(exe.resolve());rec=state.get(key)
    if not rec: raise ValueError('This game was not installed by this app. Existing mods are left alone.')
    proxy=Path(rec['proxy']); cfg=Path(rec['config'])
    if proxy.exists() and sha(proxy)!=DLL_HASH: raise ValueError('The installed DLL changed. It was not removed.')
    if cfg.exists() and sha(cfg)!=rec['config_hash']:
        raise ValueError('The configuration was changed outside this app. It was not removed; back it up or remove it manually.')
    proxy.unlink(missing_ok=True);cfg.unlink(missing_ok=True);del state[key];atomic_json(STATE,state)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('FrameGen Manager');self.geometry('850x770');self.minsize(760,680)
        self.exe=tk.StringVar();self.proxy=tk.StringVar(value='version.dll');self.mult=tk.StringVar(value='6');self.old=tk.StringVar(value='%command%');self.output=tk.StringVar();self.status=tk.StringVar(value='Choose a game and its real .exe to begin.')
        style=ttk.Style(self);style.theme_use('clam');style.configure('TButton',padding=7);style.configure('Heading.TLabel',font=('Sans',18,'bold'));style.configure('Sub.TLabel',font=('Sans',10))
        body=ttk.Frame(self,padding=20);body.pack(fill='both',expand=True)
        ttk.Label(body,text='FrameGen Manager',style='Heading.TLabel').pack(anchor='w')
        ttk.Label(body,text='MFG Unlocker for compatible Windows games on Linux / Proton',style='Sub.TLabel').pack(anchor='w',pady=(2,12))
        info='DLSS 6× requires a game with DLSS Frame Generation. Compatibility varies. Do not use with anti-cheat games. Close the game before installing.'
        ttk.Label(body,text=info,wraplength=790,justify='left').pack(anchor='w',pady=(0,12))
        ttk.Label(body,text='1. Pick an installed Steam game (optional)').pack(anchor='w')
        self.games=steam_games(); self.game=ttk.Combobox(body,values=[f'{a}  —  {b}' for a,b,_ in self.games],state='readonly');self.game.pack(fill='x',pady=(3,9));self.game.bind('<<ComboboxSelected>>',self.game_selected)
        ttk.Label(body,text='2. Select the actual game executable (.exe)').pack(anchor='w')
        row=ttk.Frame(body);row.pack(fill='x',pady=(3,9));ttk.Entry(row,textvariable=self.exe).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Browse…',command=self.browse).pack(side='left',padx=(6,0))
        row=ttk.Frame(body);row.pack(fill='x',pady=(0,10));ttk.Label(row,text='Loader name').pack(side='left');ttk.Combobox(row,textvariable=self.proxy,values=PROXIES,state='readonly',width=19).pack(side='left',padx=8);ttk.Label(row,text='Multiplier').pack(side='left',padx=(15,0));ttk.Combobox(row,textvariable=self.mult,values=('2','3','4','5','6'),state='readonly',width=5).pack(side='left',padx=8)
        ttk.Label(body,text='Cyberpunk: xinput9_1_0.dll. Other games may need a different loader; see Compatibility.',wraplength=790).pack(anchor='w',pady=(0,9))
        row=ttk.Frame(body);row.pack(fill='x');ttk.Button(row,text='Install / update multiplier',command=self.install).pack(side='left');ttk.Button(row,text='Remove managed install',command=self.remove).pack(side='left',padx=8);ttk.Button(row,text='Check status',command=self.check).pack(side='left')
        ttk.Separator(body).pack(fill='x',pady=14)
        ttk.Label(body,text='3. Steam launch options').pack(anchor='w')
        ttk.Label(body,text='Paste your game’s existing launch options below (or leave %command%). Then copy the result into Steam → game Properties → Launch Options.',wraplength=790).pack(anchor='w',pady=(3,5))
        ttk.Entry(body,textvariable=self.old).pack(fill='x');row=ttk.Frame(body);row.pack(fill='x',pady=5);ttk.Button(row,text='Generate and copy options',command=self.copy_options).pack(side='left');ttk.Button(row,text='Open compatibility guide',command=lambda:subprocess.Popen(['xdg-open','https://github.com/dashdogy/MFG-Unlocker/blob/main/docs/compatibility.md'])).pack(side='left',padx=8)
        ttk.Entry(body,textvariable=self.output,state='readonly').pack(fill='x')
        ttk.Label(body,textvariable=self.status,wraplength=790,justify='left').pack(anchor='w',pady=12)
        ttk.Label(body,text='After launching, enable DLSS Frame Generation in the game. Backspace opens the mod menu. The status file can report whether 6× was applied.',wraplength=790).pack(anchor='w')
    def game_selected(self,event=None):
        i=self.game.current()
        if i<0:return
        name,_,root=self.games[i]; self.initial=root
        self.proxy.set('xinput9_1_0.dll' if 'cyberpunk' in name.lower() else 'version.dll')
        self.status.set('Game folder selected. Browse to the actual game executable inside it.')
    def browse(self):
        p=filedialog.askopenfilename(title='Choose game executable',initialdir=str(getattr(self,'initial',Path.home())),filetypes=[('Windows executables','*.exe'),('All files','*')])
        if p:self.exe.set(p);self.check()
    def getexe(self):
        p=Path(self.exe.get()).expanduser()
        if not self.exe.get() or not p.is_file(): raise ValueError('Select a game executable first.')
        return p
    def act(self,fn):
        try:fn()
        except Exception as e:messagebox.showerror('FrameGen Manager',str(e));self.status.set(str(e))
    def install(self):
        def go():
            install(self.getexe(),self.proxy.get(),self.mult.get());self.status.set('Installed. Copy the launch options into Steam, launch the game, and check status.')
        self.act(go)
    def remove(self):
        def go():remove(self.getexe());self.status.set('Managed files removed. Remove the added CUDA and DLL override from Steam launch options too.')
        self.act(go)
    def copy_options(self):
        def go():
            s=launch_options(self.proxy.get(),self.old.get());self.output.set(s);self.clipboard_clear();self.clipboard_append(s);self.status.set('Copied. Paste into Steam Properties → Launch Options, keeping any existing options you supplied above.')
        self.act(go)
    def check(self):
        def go():
            exe=self.getexe(); p=exe.parent/'RTXMFG-Universal.status.json'
            if not p.exists():self.status.set('No mod status file yet. Launch the game after setup, then check again.');return
            d=json.loads(p.read_text());self.status.set(f"Mod status: GPU family {d.get('gpuFamily','?')}; requested {d.get('multiplier','?')}×; applied {d.get('appliedMultiplier','?')}×; active {d.get('applied',False)}; frames reported {d.get('actualFramesPresented','?')}. Status can be stale after exit.")
        self.act(go)
if __name__=='__main__': App().mainloop()
