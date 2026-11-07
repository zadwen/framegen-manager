#!/usr/bin/env python3
import sys, subprocess
from pathlib import Path
from PyQt5 import QtCore,QtWidgets
import framegen_manager as core

class Window(QtWidgets.QWidget):
 def __init__(self):
  super().__init__();self.setWindowTitle('FrameGen Manager');self.resize(850,720)
  self.setStyleSheet('QWidget { background: #151d2b; color: #e7eef7; font-size: 14px; } QLineEdit, QComboBox { background: #253246; border: 1px solid #52647b; border-radius: 5px; padding: 7px; } QPushButton { background: #2b4a63; border: 0; border-radius: 5px; padding: 9px; } QPushButton:hover { background: #396581; } QLabel#title { font-size: 27px; font-weight: bold; color: #70e4c4; }')
  v=QtWidgets.QVBoxLayout(self);v.setContentsMargins(25,22,25,22);v.setSpacing(9)
  title=QtWidgets.QLabel('FrameGen Manager');title.setObjectName('title');v.addWidget(title)
  self.label(v,'6× frame generation for compatible Windows games on Linux / Proton.')
  self.label(v,'DLSS Frame Generation support is required. Close the game first. Do not use with anti-cheat games.')
  self.label(v,'1. Choose a Steam game (optional)')
  self.games=core.steam_games();self.game=QtWidgets.QComboBox();self.game.addItem('Select an installed game…')
  for name,appid,_ in self.games:self.game.addItem(f'{name}  —  {appid}')
  self.game.currentIndexChanged.connect(self.select_game);v.addWidget(self.game)
  self.label(v,'2. Select the actual game executable (.exe)')
  row=QtWidgets.QHBoxLayout();self.exe=QtWidgets.QLineEdit();row.addWidget(self.exe);self.button(row,'Browse…',self.browse);v.addLayout(row)
  row=QtWidgets.QHBoxLayout();row.addWidget(QtWidgets.QLabel('Loader name'));self.proxy=QtWidgets.QComboBox();self.proxy.addItems(core.PROXIES);row.addWidget(self.proxy);row.addWidget(QtWidgets.QLabel('Multiplier'));self.mult=QtWidgets.QComboBox();self.mult.addItems(['2','3','4','5','6']);self.mult.setCurrentText('6');row.addWidget(self.mult);row.addStretch();v.addLayout(row)
  self.label(v,'Cyberpunk uses xinput9_1_0.dll. Other games can require a different loader name.')
  row=QtWidgets.QHBoxLayout();self.button(row,'Install / update',self.install);self.button(row,'Remove managed install',self.remove);self.button(row,'Check status',self.check);v.addLayout(row)
  self.label(v,'3. Steam launch options')
  self.label(v,'Paste your existing launch options below, then copy the result into Steam → Properties → Launch Options.')
  self.old=QtWidgets.QLineEdit('%command%');v.addWidget(self.old)
  row=QtWidgets.QHBoxLayout();self.button(row,'Generate and copy options',self.copy_options);self.button(row,'Compatibility guide',lambda:subprocess.Popen(['xdg-open','https://github.com/dashdogy/MFG-Unlocker/blob/main/docs/compatibility.md']));v.addLayout(row)
  self.output=QtWidgets.QLineEdit();self.output.setReadOnly(True);v.addWidget(self.output)
  self.status=QtWidgets.QLabel('Choose a game and its real .exe to begin.');self.status.setWordWrap(True);v.addWidget(self.status)
  self.label(v,'After launching, turn on DLSS Frame Generation in the game. Backspace opens the mod menu.')
  v.addStretch();self.initial=Path.home()
 def label(self,layout,text):
  w=QtWidgets.QLabel(text);w.setWordWrap(True);layout.addWidget(w)
 def button(self,layout,text,fn):
  b=QtWidgets.QPushButton(text);b.clicked.connect(fn);layout.addWidget(b)
 def select_game(self,i):
  if i>0:
   name,_,self.initial=self.games[i-1];self.proxy.setCurrentText('xinput9_1_0.dll' if 'cyberpunk' in name.lower() else 'version.dll');self.status.setText('Browse to the actual executable inside the selected game folder.')
 def browse(self):
  p,_=QtWidgets.QFileDialog.getOpenFileName(self,'Choose the real game executable',str(self.initial),'Windows executables (*.exe);;All files (*)')
  if p:self.exe.setText(p);self.check()
 def getexe(self):
  p=Path(self.exe.text()).expanduser()
  if not self.exe.text() or not p.is_file():raise ValueError('Select a game executable first.')
  return p
 def attempt(self,fn):
  try:fn()
  except Exception as e:self.status.setText(str(e));QtWidgets.QMessageBox.warning(self,'FrameGen Manager',str(e))
 def install(self):
  def go():core.install(self.getexe(),self.proxy.currentText(),self.mult.currentText());self.status.setText('Installed. Copy launch options into Steam, launch the game, then check status.')
  self.attempt(go)
 def remove(self):
  def go():core.remove(self.getexe());self.status.setText('Managed files removed. Remove the added CUDA and DLL override from Steam launch options too.')
  self.attempt(go)
 def copy_options(self):
  def go():
   s=core.launch_options(self.proxy.currentText(),self.old.text());self.output.setText(s);QtWidgets.QApplication.clipboard().setText(s);self.status.setText('Copied. Paste into the game’s Steam launch options.')
  self.attempt(go)
 def check(self):
  def go():
   import json,time
   p=self.getexe().parent/'RTXMFG-Universal.status.json'
   if not p.exists():self.status.setText('No status file yet. Launch the game after setup, then check again.');return
   d=json.loads(p.read_text());age=int(time.time()-p.stat().st_mtime);self.status.setText(f"Mod: requested {d.get('multiplier','?')}×; applied {d.get('appliedMultiplier','?')}×; active {d.get('applied',False)}; frames reported {d.get('actualFramesPresented','?')}. Status updated {age}s ago.")
  self.attempt(go)
app=QtWidgets.QApplication(sys.argv);window=Window();window.show();sys.exit(app.exec_())
