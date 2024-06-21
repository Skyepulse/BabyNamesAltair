# importing modules
import pandas as pd
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker
from matplotlib.backend_tools import Cursors

# preparing and formatting the data we'll need
names = pd.read_csv("../dpt2020.csv", sep=";")
names.drop(names[names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
names.drop(names[names.dpt == 'XX'].index, inplace=True)
grouped = names.groupby(['preusuel', 'annais']).agg({'nombre': 'sum'}).reset_index()
unique_names=grouped['preusuel'].unique()

# np.unique but with lists
def unique(l):
    unique_list = []
    for x in l:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

# creating empty plot
def create_initial_plot():
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title("Initial Plot")
    return fig

# When a name is selected, we update selected_names
def select_name(event, selected_names):
    selected_name = name_listbox.get(name_listbox.curselection())
    selected_names.append(selected_name)
    update_plot(selected_names)

# Updating the figure with the new selected_names list
def update_plot(selected_names):
    fig.clear()
    ax = fig.add_subplot(111)
    selected_names=unique(selected_names)

    lines = []
    for name in selected_names:
        data = grouped[grouped['preusuel'] == name]
        x = list(data["annais"])        
        y = list(data["nombre"])

        # we make sure to have values for all years
        for year in range(1900,2020):
            if str(year) not in x:
                x.append(year)
                y.append(0)

        sorted_lists = sorted(zip(map(int, x), y)) # we sort the lists according to the year
        x,y=zip(*sorted_lists)

        line, = ax.plot(x, y, label=name, picker=5)
        lines.append(line)

    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.set_title("Name popularity as a function of time")
    ax.legend()  # Add legend to differentiate curves
    canvas.draw()

    # remove one name when clicking on line
    def onpick(event):
        if event.artist in lines:
            lines.remove(event.artist)
            global selected_names
            selected_names.remove(event.artist.get_label())
            event.artist.remove()
            update_plot(selected_names)
    
    fig.canvas.mpl_connect('pick_event', onpick)

    # special pointer when hovering line
    def on_hover(event):
        if event.inaxes:
            for line in lines:
                cont, ind = line.contains(event)
                if cont:
                    fig.canvas.set_cursor(Cursors.HAND)
                    return
        fig.canvas.set_cursor(Cursors.POINTER)


    fig.canvas.mpl_connect('motion_notify_event', on_hover)

# Resetting the names selected
def reset_plot():
    global selected_names
    fig.clear()
    selected_names=[]
    canvas.draw()

# Based on search query, we 
def update_listbox(event):
    searched = search_entry.get().upper()
    name_listbox.delete(0, tk.END)

    for name in unique_names:
        if searched in name:
            name_listbox.insert(tk.END, name)

root = tk.Tk()
root.title("Matplotlib Plot in Tkinter")

selected_names = []

# Canvas frame on the left
plot_frame = ttk.Frame(root)
plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

# canvas for plotting
fig = create_initial_plot()
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# "Button" frame on the right
button_frame = ttk.Frame(root, width=400)
button_frame.pack(side=tk.RIGHT, fill=tk.Y)
button_frame.pack_propagate(False)

label = ttk.Label(button_frame, text="Select a Name:")
label.pack(pady=10)

# Search query thing
search_entry = ttk.Entry(button_frame)
search_entry.pack(pady=10, padx=10, fill=tk.X)

# Listbox with a scrollbar
scrollbar = ttk.Scrollbar(button_frame, orient=tk.VERTICAL)
name_listbox = tk.Listbox(button_frame, yscrollcommand=scrollbar.set, height=5)

for name in unique_names:
    name_listbox.insert(tk.END, name)

scrollbar.config(command=name_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
name_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

# Binding
search_entry.bind("<KeyRelease>", update_listbox)
name_listbox.bind("<Double-Button-1>", lambda event: select_name(event, selected_names))

# Reset button
reset_button = ttk.Button(button_frame, text="Reset", command=reset_plot)
reset_button.pack(pady=30, padx=20)


root.mainloop()