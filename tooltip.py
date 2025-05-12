from tkinter import *
from tkinter import ttk

class tooltip:
    preinstall={
        'select_mode': '1.积分模式：...；\n2.微分模式：...'
        }
    
    def create_tooltip(widget, text):
        tooltip = None

        def show_tooltip(event):
            nonlocal tooltip
            if tooltip is None :
                tooltip = Toplevel(widget)
                tooltip.wm_overrideredirect(True)
                tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
                label = Label(tooltip, text=text, background="yellow",
                              relief="solid", borderwidth=1, font=("Arial", 10))
                label.pack()

        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip is not None:
                tooltip.destroy()
                tooltip = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

if __name__ == '__main__':
    print('这玩意直接运行没啥效果（）')