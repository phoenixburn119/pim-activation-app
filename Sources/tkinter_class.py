import time
import tkinter as tk
from tkinter import ttk
# import ttkbootstrap as tb
# from ttkbootstrap.scrolled import ScrolledText
from tkinter import PhotoImage
from Sources.graph_class import *
import threading 

class TKClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pim-Management-Toolkit")
        self.geometry("1000x500")
        self.config(background="grey")
        # icon = PhotoImage(file='pimicon.png')
        # self.iconphoto(False, icon)
        
        self.graphcl = graph_initialize() # Initializes graph class.
        
        # Create left and right frames
        left_frame = tk.Frame(self,  bg='grey')
        left_frame.pack(side='left',  fill=tk.BOTH,  padx=10,  pady=5,  expand=True)
        right_frame  =  tk.Frame(self,  bg='grey')
        right_frame.pack(side='right',  fill=tk.Y,  padx=10,  pady=5,  expand=True)
        self.HomeLabel = ttk.Label(left_frame, text=f"PIM Checkout Tool BETA Build: No active user", anchor="center", justify="center")
        self.HomeLabel.pack(side='top', fill="x")
        
        left_sub_frame  =  tk.Frame(left_frame,  bg='blue')
        left_sub_frame.pack(side='top',  fill='both')
        
        loginbutton = tk.Button(left_sub_frame, text="Azure Login", anchor='center', command=lambda:threading.Thread(target=self.azure_login).start())
        # loginbutton = tk.Button(left_sub_frame, text="Azure Login", anchor='center', command=lambda:self.azure_login())
        loginbutton.pack(side="left", anchor=tk.CENTER, fill='both', padx=4, expand=True)
        
        self.refresh_roles_button = tk.Button(left_sub_frame, text="Refesh Roles", anchor='center', command=lambda:threading.Thread(target=self.update_rolelist).start())
        self.refresh_roles_button.pack(side='left', anchor=tk.NW, fill='both', padx=4, expand=True)
        
        checkout_roles_button = tk.Button(left_sub_frame, text="Activate Roles", anchor='center', command=lambda:threading.Thread(target=self.tk_checkout_roles).start())
        checkout_roles_button.pack(side="left", anchor=tk.NW, fill='both', padx=4, expand=True)
        
        self.roleslist = tk.Listbox(left_frame, selectmode='multiple', height= 27)
        self.roleslist.pack(side='top', fill="both")
        self.roleslist.insert(tk.END, "Roles go here. Please log into Azure first.")
        SpacerLabel = ttk.Label(left_frame, text=f"_______________________________________________________________________", anchor="center", justify="center", background='grey', foreground='grey')
        SpacerLabel.pack(side='top', fill="x")
        
        self.outputtext = tk.Text(right_frame, width=200, height=30)
        # self.outputtext = ScrolledText(right_frame, width=200, height=28, wrap=tb.WORD)
        self.outputtext.pack(side='top', fill='both')

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
            # self.refresh_roles_button.config(state='active')
            self.refresh_roles_button.config(state='normal')
    
    def azure_login(self):
        result = self.graphcl.get_auth()
        # self.outputtext.insert(tk.END, result['Status'])
        if result['Status'] == "Token failed":
            self.outputtext.insert(tk.END, f"There was an issue retrieving your token. Please contact an administrator to verify proper permissions and you're using your correct cloud account.")
            self.outputtext.see('end')
            return
        self.outputtext.insert(tk.END, "User has been logged into Azure. Refreshing roles automatically.")
        self.outputtext.see('end')
        me = self.graphcl.get_personaldata()
        self.HomeLabel.config(text=f"PIM Checkout Tool | Active User ({me['displayName']})")
        self.update_rolelist()