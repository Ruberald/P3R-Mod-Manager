import json, os, re, shutil, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

EXTS = {".pak", ".ucas", ".utoc"}

def norm(p):
    return re.sub(r"[^a-z0-9]", "", p.stem.lower())

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("P3R Mod Manager")
        self.geometry("960x650")
        self.home = Path(__file__).resolve().parent
        self.mods = self.home / "mods"; self.mods.mkdir(exist_ok=True)
        self.data = self.home / "manager_data"; self.data.mkdir(exist_ok=True)
        try: self.state = json.loads((self.data/"state.json").read_text())
        except Exception: self.state = {"mods":{}}
        self.scanvar = tk.StringVar(value=self.state.get("scan_root", str(Path.home()/"Downloads")))
        self.gamevar = tk.StringVar(value=self.state.get("game_paks", ""))
        self.status = tk.StringVar(value="Select Downloads and scan.")
        self.found = {}
        self.ui(); self.refresh()

    def save(self):
        self.state["scan_root"] = self.scanvar.get()
        self.state["game_paks"] = self.gamevar.get()
        (self.data/"state.json").write_text(json.dumps(self.state, indent=2))

    def ui(self):
        f=ttk.Frame(self,padding=12); f.pack(fill="both",expand=True)
        ttk.Label(f,text="P3R Mod Manager",font=("Segoe UI",17,"bold")).pack(anchor="w")
        ttk.Label(f,text="Recursively discovers extracted Unreal mod packages.").pack(anchor="w",pady=(0,8))
        a=ttk.LabelFrame(f,text="Discover mods",padding=8); a.pack(fill="x")
        r=ttk.Frame(a); r.pack(fill="x")
        ttk.Entry(r,textvariable=self.scanvar).pack(side="left",fill="x",expand=True)
        ttk.Button(r,text="Browse",command=self.browse_scan).pack(side="left",padx=5)
        ttk.Button(r,text="Scan recursively",command=self.scan).pack(side="left")
        b=ttk.LabelFrame(f,text="Discovered packages",padding=6); b.pack(fill="both",expand=True,pady=8)
        self.ft=ttk.Treeview(b,columns=("name","count","path"),show="headings",selectmode="extended")
        for c,t,w in [("name","Package",260),("count","Files",65),("path","Folder",560)]:
            self.ft.heading(c,text=t); self.ft.column(c,width=w)
        self.ft.pack(fill="both",expand=True)
        rr=ttk.Frame(f); rr.pack(fill="x")
        ttk.Button(rr,text="Import selected",command=self.import_selected).pack(side="left")
        ttk.Button(rr,text="Import all",command=self.import_all).pack(side="left",padx=6)
        c=ttk.LabelFrame(f,text="Game Paks directory",padding=8); c.pack(fill="x",pady=8)
        ttk.Entry(c,textvariable=self.gamevar).pack(side="left",fill="x",expand=True)
        ttk.Button(c,text="Browse",command=self.browse_game).pack(side="left",padx=5)
        ttk.Button(c,text="Open ~mods",command=self.open_mods).pack(side="left")
        d=ttk.LabelFrame(f,text="Imported mod library",padding=6); d.pack(fill="both",expand=True)
        self.lt=ttk.Treeview(d,columns=("enabled","name","files"),show="headings",selectmode="extended",height=7)
        for c,t,w in [("enabled","Enabled",75),("name","Mod",550),("files","Files",70)]:
            self.lt.heading(c,text=t); self.lt.column(c,width=w)
        self.lt.pack(fill="both",expand=True)
        rr=ttk.Frame(f); rr.pack(fill="x",pady=7)
        ttk.Button(rr,text="Refresh",command=self.refresh).pack(side="left")
        ttk.Button(rr,text="Enable selected",command=lambda:self.toggle(True)).pack(side="left",padx=(12,4))
        ttk.Button(rr,text="Disable selected",command=lambda:self.toggle(False)).pack(side="left")
        ttk.Button(rr,text="Enable all",command=lambda:self.all(True)).pack(side="left",padx=(12,4))
        ttk.Button(rr,text="Disable all",command=lambda:self.all(False)).pack(side="left")
        ttk.Label(f,textvariable=self.status,relief="sunken",padding=5).pack(fill="x")

    def browse_scan(self):
        p=filedialog.askdirectory(title="Choose Downloads or extracted mods")
        if p:self.scanvar.set(p);self.save()
    def browse_game(self):
        p=filedialog.askdirectory(title="Select P3R Content/Paks")
        if p:
            p=Path(p)
            if p.name.lower()=="content":p=p/"Paks"
            self.gamevar.set(str(p));self.save()
    def target(self):
        p=Path(self.gamevar.get()).expanduser()
        if not p.is_dir():
            messagebox.showerror("P3R Mod Manager","Select the existing P3R Content/Paks directory.")
            return None
        if p.name.lower()=="content":p=p/"Paks"
        if not p.is_dir():
            messagebox.showerror("P3R Mod Manager",f"Paks folder not found: {p}");return None
        return p/"~mods"
    def open_mods(self):
        p=self.target()
        if p:p.mkdir(exist_ok=True);os.startfile(str(p))
    def discover(self,root):
        groups={}
        for folder,dirs,files in os.walk(root):
            dirs[:]=[d for d in dirs if d not in {".git","__pycache__"}]
            folder=Path(folder)
            for name in files:
                p=folder/name
                if p.suffix.lower() in EXTS:
                    groups.setdefault((str(folder),norm(p)),[]).append(p)
        out=[]
        for (folder,stem),files in groups.items():
            pak=[p for p in files if p.suffix.lower()==".pak"]
            for anchor in pak:
                bundle=[anchor]+[p for p in files if p!=anchor and norm(p)==norm(anchor)]
                out.append({"name":anchor.stem,"files":bundle,"folder":Path(folder)})
        return sorted(out,key=lambda x:(x["name"].lower(),str(x["folder"]).lower()))
    def scan(self):
        root=Path(self.scanvar.get()).expanduser()
        if not root.is_dir():messagebox.showerror("P3R Mod Manager","Scan folder does not exist.");return
        self.ft.delete(*self.ft.get_children());self.found={}
        for i,p in enumerate(self.discover(root)):
            key=str(i);self.found[key]=p
            self.ft.insert("","end",iid=key,values=(p["name"],len(p["files"]),str(p["folder"])))
        self.save();self.status.set(f"Found {len(self.found)} package(s).")
        if not self.found:messagebox.showinfo("P3R Mod Manager","No extracted .pak packages found. This version does not unpack .7z files.")
    def import_selected(self):
        ids=self.ft.selection()
        if not ids:messagebox.showinfo("P3R Mod Manager","Select packages first.");return
        self.import_packages([self.found[i] for i in ids])
    def import_all(self):
        self.import_packages(list(self.found.values()))
    def import_packages(self,items):
        done=0;skipped=[]
        for item in items:
            name=item["name"];dest=self.mods/name
            if dest.exists():skipped.append(name+" (already imported)");continue
            dest.mkdir()
            try:
                for p in item["files"]:shutil.copy2(p,dest/p.name)
                done+=1
            except OSError as e:shutil.rmtree(dest,ignore_errors=True);skipped.append(name+": "+str(e))
        self.refresh()
        msg=f"Imported {done} package(s)."
        if skipped:msg+="\n\nSkipped:\n"+"\n".join(skipped[:20])
        messagebox.showinfo("P3R Mod Manager",msg)
    def refresh(self):
        self.lt.delete(*self.lt.get_children())
        for d in sorted(self.mods.iterdir()):
            if not d.is_dir():continue
            files=list(d.glob("*"))
            if not files:continue
            rec=self.state.setdefault("mods",{}).setdefault(d.name,{"enabled":False,"installed":[]})
            self.lt.insert("","end",iid=d.name,values=("Yes" if rec["enabled"] else "No",d.name,len(files)))
        self.save()
    def toggle(self,enable):
        names=list(self.lt.selection())
        if not names:messagebox.showinfo("P3R Mod Manager","Select mods first.");return
        self.deploy(names,enable)
    def all(self,enable):
        self.deploy([p.name for p in self.mods.iterdir() if p.is_dir()],enable)
    def deploy(self,names,enable):
        target=self.target()
        if target is None:return
        target.mkdir(exist_ok=True);errors=[];changed=0
        for name in names:
            folder=self.mods/name
            rec=self.state.setdefault("mods",{}).setdefault(name,{"enabled":False,"installed":[]})
            files=[p for p in folder.rglob("*") if p.is_file()]
            if enable:
                conflicts=[p.name for p in files if (target/p.name).exists() and p.name not in rec["installed"]]
                if conflicts:errors.append(name+": conflict: "+", ".join(conflicts[:5]));continue
                copied=[]
                try:
                    for p in files:shutil.copy2(p,target/p.name);copied.append(p.name)
                    rec["installed"]=copied;rec["enabled"]=True;changed+=1
                except OSError as e:
                    for n in copied:
                        try:(target/n).unlink()
                        except OSError:pass
                    errors.append(name+": "+str(e))
            else:
                for n in rec["installed"]:
                    dest=target/n
                    try:
                        if dest.is_file():dest.unlink()
                    except OSError as e:errors.append(name+": "+str(e))
                rec["installed"]=[];rec["enabled"]=False;changed+=1
        self.save();self.refresh()
        msg=f"{'Enabled' if enable else 'Disabled'} {changed} mod(s)."
        if errors:messagebox.showwarning("P3R Mod Manager",msg+"\n\n"+"\n".join(errors))
        self.status.set(msg)

if __name__=="__main__":App().mainloop()
