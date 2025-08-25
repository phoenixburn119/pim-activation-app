from Sources.graph_class import *
import tkinter as tk
from tkinter import ttk
from tkinter import *
# from PIL import Image, ImageTk
import threading
import sys
import time
import os
# import ttkbootstrap as tb
# from ttkbootstrap.scrolled import ScrolledText

class TKClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pim-Management-Toolkit")
        self.geometry("1000x500")
        self.config(background="grey")
        try:
            self.iconbitmap(sys.executable)
        except:
            print("Icon setting failed")
            
        self.graphcl = graph_initialize() # Initializes graph class.
        
        pim_menu = Menu(self)
        self.config(menu=pim_menu)

        pim_menu.add_command(label='Azure Login', command=lambda:threading.Thread(target=self.azure_login).start())
        
        mode_menu = Menu(pim_menu)
        pim_menu.add_cascade(label="PIM Mode Selector", menu=mode_menu)
        mode_menu.add_command(label='Entra Roles', command=lambda: self.show_frame(RolesFrame), accelerator="Ctrl+Q")
        mode_menu.add_command(label='Groups', command=lambda: self.show_frame(GroupsFrame), accelerator="Ctrl+W")  
        mode_menu.add_command(label='Azure Resources', command=lambda: self.show_frame(ResourcesFrame), accelerator="Ctrl+E")
        
        pim_menu.add_command(label="App Info", command=lambda:threading.Thread(target=self.show_info_popup).start())
        
        self.bind("<Control-q>", self.show_role)
        self.bind("<Control-w>", self.show_group)
        self.bind("<Control-e>", self.show_resources)

        self.columnconfigure(0, weight= 1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight= 1)
        container.rowconfigure(0, weight=1)

        self.outputtext = tk.Text(self, background="gray92")
        self.outputtext.grid(row=0, column=1, sticky='nsew')


        self.frames = {}

        for F in (RolesFrame, GroupsFrame, ResourcesFrame):
            frame = F(
                container,
                self.outputtext,
                self.graphcl,
            )
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(RolesFrame)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        
    def show_info_popup(self):
        message = Toplevel(self)
        message.geometry("300x200")
        message.title("PIM-Management-Toolkit Info")
        info_label = tk.Label(message, text="App version v2.8.4, release date 8/25/2025. Contact #### for any support questions.", wraplength=200)
        info_label.pack(side="top", fill="both", expand=True)
        update_info_label = tk.Label(message, text="Version Changes: Fixes for various activation lag and freezing. Added function to activate roles that require reauth. Fixed reauth opening multiple tabs when activating 2 or more roles that require reauth.   KNOWN ISSUES: N/A for now", wraplength=200)
        update_info_label.pack(side="top", fill="both", expand=True)

    def show_role(self, event=None):
        self.show_frame(RolesFrame)
        threading.Thread(target=self.frames[RolesFrame].update_rolelist).start()
        # self.frames[GroupsFrame].update_grouplist() 
    def show_group(self, event=None):
        self.show_frame(GroupsFrame)
        threading.Thread(target=self.frames[GroupsFrame].update_grouplist).start()
        # self.frames[RolesFrame].update_rolelist()
    def show_resources(self, event=None):
        self.show_frame(ResourcesFrame)
        threading.Thread(target=self.frames[ResourcesFrame].update_resourcelist).start()
        # self.frames[GroupsFrame].update_resourcelist()

    def azure_login(self):
        result = self.graphcl.get_auth()
        # self.outputtext.insert(tk.END, result['Status'])
        if result['Status'] == "Token failed":
            self.outputtext.insert(tk.END, f"There was an issue retrieving your token. Please contact an administrator to verify proper permissions and you're using your correct cloud account.")
            self.outputtext.see('end')
            return
        self.outputtext.insert(tk.END, "User has been logged into Azure. Refreshing roles automatically.")
        self.outputtext.see('end')
        # me = self.graphcl.get_personaldata()
        # self.HomeLabel.config(text=f"PIM Checkout Tool | Active User ({me['displayName']})")
        # RolesFrame.update_rolelist()
        self.frames[RolesFrame].update_rolelist()
        
class RolesFrame(tk.Frame):
    def __init__(self, parent, outputtext, graphcl):
        super().__init__(parent)
        self.outputtext = outputtext
        self.graphcl = graphcl
        # self.grid(sticky="nsew")
        left_sub_frame  =  tk.Frame(self,  bg='blue')
        left_sub_frame.pack(side='top',  fill='both')
        self.refresh_roles_button = tk.Button(left_sub_frame, text="Refesh Roles", anchor='center', command=lambda:threading.Thread(target=self.update_rolelist).start())
        self.refresh_roles_button.pack(side='left', anchor=tk.NW, fill='both', padx=4, expand=True)
        checkout_roles_button = tk.Button(left_sub_frame, text="Activate Roles", anchor='center', command=lambda:threading.Thread(target=self.tk_checkout_roles).start())
        checkout_roles_button.pack(side="right", anchor=tk.NW, fill='both', padx=4, expand=True)
        
        self.roleslist = tk.Listbox(self, selectmode='multiple', height= 27, width= 40)
        self.roleslist.pack(side='top', fill="both", expand=True)
        self.roleslist.insert(tk.END, "Roles go here. Please log into Azure first.")
        
    def update_rolelist(self):
        try:
            self.refresh_roles_button.config(state='disabled')
            self.roleslist.delete(0, tk.END)
            self.outputtext.insert(tk.END, '\n' + "Roles updating please wait...")
            self.outputtext.see('end')
            all_roles = self.graphcl.get_roles()
            all_list = []
            active_roles = self.graphcl.get_active_roles()
            active_list = []
            for e in (all_roles['value']):
                all_list.append(e['roleDefinition']['displayName'])
            for e in (active_roles['value']):
                active_list.append(e['roleDefinition']['displayName'])
            if all_list == []:
                self.outputtext.insert(tk.END, '\n' + "Either token has expired or a permissions issue exists. Please try to log back into Azure if app has been open and logged in for over 60 minutes.")
                self.outputtext.see('end')
                self.refresh_roles_button.config(state='normal')
                return
            index = 0
            for l in all_list:
                if l in active_list:
                    self.roleslist.insert(tk.END, l+ " (Active)")
                    self.roleslist.itemconfig(index,{'bg':'OliveDrab2'})
                else:
                    self.roleslist.insert(tk.END, l)
                index += 1
            self.outputtext.insert(tk.END, '\n' + "Roles updated.")
            self.outputtext.see('end')
            self.refresh_roles_button.config(state='normal')
        except:
            self.outputtext.insert(tk.END, '\n' + "Either token has expired or a permissions issue exists. Please try to log back into Azure if app has been open and logged in for over 60 minutes.")
            self.outputtext.see('end')
            # self.refresh_roles_button.config(state='active')
            self.refresh_roles_button.config(state='normal')
            
    def tk_checkout_roles(self):
        try:
            rlist = []
            for i in self.roleslist.curselection():
                rlist.append(self.roleslist.get(i))
            # print(rlist)
            
            thread_list = []
            for i in rlist:
                t = threading.Thread(target=self.worker_function, args=(i,), daemon=True)
                thread_list.append(t)
                t.start()
                
            while any(t.is_alive() for t in thread_list):
                time.sleep(.5)
            self.update_rolelist()
        except Exception as e:
            self.outputtext.insert(tk.END, '\n' + f"Checkout a Token or create a new one after previous expired : {e}")
            self.outputtext.see('end')
            
    def worker_function(self, role: str):
        self.outputtext.insert(tk.END, '\n' + f"Adding {role} to checkout queue, please wait...")
        response = self.graphcl.checkout_roles(role)
        if response['Status'] == "Checkout Failed":
            self.outputtext.insert(tk.END, '\n' + f"Checkout a Token or create a new one after previous expired | Error: {response['Error']}")
            self.outputtext.see('end')
        elif response['Status'] == "Checkout Succeeded":
            self.outputtext.insert(tk.END, '\n' + f"{role}: Checkout Complete")
            self.outputtext.see('end')
        else:
            # print(f"error unknown | {response['Error']}")
            self.outputtext.insert(tk.END, '\n' + f"error unknown | {response['Error']}")
        
class GroupsFrame(tk.Frame):
    def __init__(self, parent, outputtext, graphcl):
        super().__init__(parent)
        self.outputtext = outputtext
        self.graphcl = graphcl
        # self.grid(sticky="nsew")
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        left_sub_frame  =  tk.Frame(self,  bg='blue')
        left_sub_frame.pack(side='top',  fill='both')
        self.groups_button = ttk.Button(left_sub_frame, text="Refresh Groups", command=lambda:threading.Thread(target=self.update_grouplist).start())
        self.groups_button.pack(side='top', fill='both')
        
        self.grouplist = tk.Listbox(left_sub_frame, selectmode='extended', height= 27)
        self.grouplist.pack(side='top', fill="both", expand=True)
        self.grouplist.insert(tk.END, "Groups go here. Please log into Azure first.")
        
    def update_grouplist(self):
        try:
            self.groups_button.config(state='disabled')
            self.grouplist.delete(0, tk.END)
            self.outputtext.insert(tk.END, '\n' + "Groups updating please wait...")
            all_roles = self.graphcl.get_groups()
            all_list = []
            active_roles = self.graphcl.get_active_groups()
            active_list = []
            for e in (all_roles['value']):
                all_list.append(e['group']['displayName'])
            for e in (active_roles['value']):
                active_list.append(e['group']['displayName'])
            if all_list == []:
                # self.outputtext.insert(tk.END, '\n' + "Either token has expired or a permissions issue exists. Please try to log back into Azure if app has been open and logged in for over 60 minutes.")
                # self.outputtext.see('end')
                self.groups_button.config(state='normal')
                return
            index = 0
            for l in all_list:
                if l in active_list:
                    self.grouplist.insert(tk.END, l+ " (Active)")
                    self.grouplist.itemconfig(index,{'bg':'OliveDrab2'})
                else:
                    self.grouplist.insert(tk.END, l)
                index += 1
            self.outputtext.insert(tk.END, '\n' + "Groups updated.")
            self.outputtext.see('end')
            self.groups_button.config(state='normal')
        except Exception as e:
            self.outputtext.insert(tk.END, '\n' + f"Either token has expired or a permissions issue exists. Please try to log back into Azure if app has been open and logged in for over 60 minutes. {e}")
            self.outputtext.see('end')
            # self.refresh_roles_button.config(state='active')
            self.groups_button.config(state='normal')
       
class ResourcesFrame(tk.Frame):
    def __init__(self, parent, outputtext, graphcl):
        super().__init__(parent)
        self.outputtext = outputtext
        self.graphcl = graphcl
        # self.grid(sticky="nsew")
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        left_sub_frame  =  tk.Frame(self,  bg='chartreuse4')
        left_sub_frame.pack(side='top',  fill='both')
        self.groups_button = tk.Button(left_sub_frame, text="Refresh Resources", command=lambda:threading.Thread(target=self.update_resourcelist).start())
        self.groups_button.pack(side='left', fill='both', anchor=tk.NW, padx=4, expand=True)
        checkout_resources_button = tk.Button(left_sub_frame, text="Activate Resources", anchor='center', command=lambda:threading.Thread(target=self.tk_checkout_resources).start())
        checkout_resources_button.pack(side="right", anchor=tk.NW, fill='both', padx=4, expand=True)
        
        self.resourcelist = tk.Listbox(self, selectmode='extended', height= 27)
        self.resourcelist.pack(side='top', fill="both", expand=True)
        self.resourcelist.insert(tk.END, "Resources go here. Please log into Azure first.")
        
    def update_resourcelist(self):
        try:
            self.groups_button.config(state='disabled')
            self.resourcelist.delete(0, tk.END)
            self.outputtext.insert(tk.END, '\n' + "Resources updating please wait...")
            all_roles = self.graphcl.get_resources()
            all_list = []
            active_roles = self.graphcl.get_active_resources()
            active_list = []
            for e in (all_roles['value']):
                all_list.append(e['resource']['displayName'])
            for e in (active_roles['value']):
                active_list.append(e['displayName'])
            if all_list == []:
                # self.outputtext.insert(tk.END, '\n' + "Either token has expired or a permissions issue exists. Please try to log back into Azure if app has been open and logged in for over 60 minutes.")
                # self.outputtext.see('end')
                self.groups_button.config(state='normal')
                return
            
            index = 0
            for l in all_list:
                rlist = self.resourcelist.get(0,END)
                if (l + " (Active)") in rlist:
                    print(f"Dupe Entry : {l}")
                else:
                    if l in active_list:
                        self.resourcelist.insert(tk.END, l+ " (Active)")
                        self.resourcelist.itemconfig(index,{'bg':'OliveDrab2'})
                    else:
                        self.resourcelist.insert(tk.END, l)
                    index += 1
                
            self.outputtext.insert(tk.END, '\n' + "Resources updated. If resource is not active, wait 15 seconds and refresh.")
            self.outputtext.see('end')
            self.groups_button.config(state='normal')
        except Exception as e:
            self.outputtext.insert(tk.END, '\n' + f"Either token has expired or a permissions issue exists. Please try to log back into Azure if app has been open and logged in for over 60 minutes. {e}")
            self.outputtext.see('end')
            # self.refresh_roles_button.config(state='active')
            self.groups_button.config(state='normal')
            
    def tk_checkout_resources(self):
        try:
            rlist = []
            for i in self.resourcelist.curselection():
                rlist.append(self.resourcelist.get(i))
            print(rlist)
            
            thread_list = []
            for i in rlist:
                t = threading.Thread(target=self.worker_function, args=(i,), daemon=True)
                thread_list.append(t)
                t.start()
                
            while any(t.is_alive() for t in thread_list):
                time.sleep(.5)
            self.update_resourcelist()
        except Exception as e:
            self.outputtext.insert(tk.END, '\n' + f"Checkout a Token or create a new one after previous expired : {e}")
            self.outputtext.see('end')
            
    def worker_function(self, role: str):
        self.outputtext.insert(tk.END, '\n' + f"Adding {role} to checkout queue, please wait...")
        response = self.graphcl.checkout_resources(role)
        if response['Status'] == "Checkout Failed":
            self.outputtext.insert(tk.END, '\n' + f"Checkout a Token or create a new one after previous expired | Error: {response['Error']}")
            self.outputtext.see('end')
        elif response['Status'] == "Checkout Succeeded":
            self.outputtext.insert(tk.END, '\n' + f"{role}: Checkout Complete")
            self.outputtext.see('end')
        else:
            # print(f"error unknown | {response['Error']}")
            self.outputtext.insert(tk.END, '\n' + f"error unknown | {response['Error']}")