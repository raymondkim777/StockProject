from Stock import Stock

import sqlite3
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from math import sin, cos, pi, floor, ceil, sqrt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from time import sleep


class StockGUI:
    def __init__(self, allStockList: list, timePeriod: tuple):
        self.conn = sqlite3.connect("StockDatabase.db")
        self.cur = self.conn.cursor()

        self.allStockList = allStockList
        self.timePeriod = timePeriod

    def __findRelationBounds(self):
        # find company relation bounds
        query = f"{self.allStockList[0].companyName}, {self.allStockList[1].companyName}"
        self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")

        global maxRelScore, minRelScore
        maxRelScore = minRelScore = float(self.cur.fetchone()[0])

        for i in range(len(self.allStockList)):
            for j in range(len(self.allStockList)):
                if i != j:
                    com1 = self.allStockList[i].companyName
                    com2 = self.allStockList[j].companyName
                    query = f"{com1}, {com2}"
                    self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")
                    result = float(self.cur.fetchone()[0])
                    maxRelScore = max(maxRelScore, result)
                    minRelScore = min(minRelScore, result)

    def runGUI(self) -> None:
        """
        Runs stock GUI to display all results, including raw stock data increase,
        company relation values, and prediction values.

        :return: None
        """

        self.__findRelationBounds()

        global root

        stock_inc = []
        for stock in self.allStockList:
            stock_inc.append((stock.stockChangeDataShort[-1] / stock.stockDataShort[-2]) * 100)

        # set fonts
        default_font = 'Calibri 16'

        # parameters
        frame_widths = [600, 700, 800]
        gui_width = sum(frame_widths) + 20
        gui_height = 900

        # tkinter
        root = Tk()
        root.title("Stock Prediction Program")
        root.geometry(f'{gui_width}x{gui_height}')

        allFrame = Frame(root, height=gui_height, width=gui_width)
        allFrame.place(relx=0.5, rely=0.5, anchor=CENTER)

        # sub frames
        subFrame1 = Frame(allFrame, height=gui_height, width=frame_widths[0])
        subFrame1.grid(row=0, column=0)

        subFrame2 = Frame(allFrame, height=gui_height, width=frame_widths[1])
        subFrame2.grid(row=0, column=1)

        subFrame3 = Frame(allFrame, height=gui_height, width=frame_widths[2])
        subFrame3.grid(row=0, column=2)

        # subframe1 contents
        canvas_head_height = 60
        canvas_row_height = 40
        canvas_bottom_padding = 20
        frame1bt_height = 60

        subFrame1CanvasFrame = Frame(
            subFrame1, height=gui_height - frame1bt_height, width=frame_widths[0] - 20, bg='orange')
        subFrame1CanvasFrame.grid(row=0, column=0)

        subFrame1Canvas = Canvas(
            subFrame1CanvasFrame, height=gui_height - frame1bt_height, width=frame_widths[0] - 20, bg='white')
        subFrame1Canvas.grid(row=0, column=0)

        canvasScrollbar = Scrollbar(subFrame1CanvasFrame, orient=VERTICAL, command=subFrame1Canvas.yview)
        canvasScrollbar.grid(row=0, column=1, sticky='ns')

        subFrame1Canvas.bind('<Enter>', lambda event: self.__bound_to_mousewheel(event, subFrame1Canvas))
        subFrame1Canvas.bind('<Leave>', lambda event: self.__unbound_to_mousewheel(event, subFrame1Canvas))

        subFrame1Canvas.config(yscrollcommand=canvasScrollbar.set)
        subFrame1Canvas.configure(scrollregion=subFrame1Canvas.bbox(ALL))

        # subframe1 canvas contents
        canvas_col_x = [100, 260, 400, 520]

        subFrame1Canvas.create_rectangle(0, 0, frame_widths[0], canvas_head_height, fill='#E2E2E2', width=0)
        subFrame1Canvas.create_text(canvas_col_x[0], canvas_head_height / 2, text="Company", font=default_font)
        subFrame1Canvas.create_text(canvas_col_x[1], canvas_head_height / 2, text="Symbol", font=default_font)
        subFrame1Canvas.create_text(canvas_col_x[2], canvas_head_height / 2, text="Stock", font=default_font)
        subFrame1Canvas.create_text(canvas_col_x[3], canvas_head_height / 2, text="Focus", font=default_font)

        mainStockVar = IntVar()
        for i in range(len(self.allStockList)):
            subFrame1Canvas.create_text(
                canvas_col_x[0], canvas_head_height * 1.5 + i * canvas_row_height,
                text=self.allStockList[i].companyName, font=default_font)
            subFrame1Canvas.create_text(
                canvas_col_x[1], canvas_head_height * 1.5 + i * canvas_row_height,
                text=self.allStockList[i].stockName, font=default_font)
            if stock_inc[i] >= 0:
                stockColor = 'green'
            else:
                stockColor = 'red'
            subFrame1Canvas.create_text(canvas_col_x[2], canvas_head_height * 1.5 + i * canvas_row_height,
                                        text="+" * ('-' not in str(stock_inc[i])) + f"{stock_inc[i]:.2f}%",
                                        fill=stockColor, font=default_font)

            radio = Radiobutton(root, variable=mainStockVar, value=i + 1, width=0, bg='white')
            subFrame1Canvas.create_window(
                canvas_col_x[3], canvas_head_height * 1.5 + i * canvas_row_height, anchor=CENTER, window=radio)

        subFrame1CanvasBounds = list(subFrame1Canvas.bbox(ALL))
        subFrame1CanvasBounds[3] += canvas_bottom_padding
        # noinspection PyTypeChecker
        subFrame1Canvas.configure(scrollregion=subFrame1CanvasBounds)

        # subframe1 buttons
        subFrame1BtFrame = Frame(subFrame1, height=frame1bt_height, width=frame_widths[0], bg='white')
        subFrame1BtFrame.grid(row=1, column=0)

        showAllRelBt = Button(
            subFrame1BtFrame, text="Show All Relations", padx=2, pady=2, width=20, command=self.__displayResults)
        showAllRelBt.place(relx=0.25, rely=0.5, anchor=CENTER)

        showSpecAnBt = Button(
            subFrame1BtFrame, text="Show Focus Details", padx=2, pady=2, width=20,
            command=lambda: self.__displaySpecificResults(
                mainStockVar.get(), [
                    subFrame2Canvas, [
                        canvas_title_font, canvas_axis_font, canvas_font, title_yoffset, legend_width, legend_xpad,
                        legend_ypad, legend_labelpad, axis_end_padding, axis_side_padding, x_label_xoffset,
                        x_label_yoffset, y_label_xoffset, highlight_position, highlight_height, y_axis_offset,
                        graph_top_start, graph_bottom_padding, highlight_width], stock_inc
                ], [
                    priceLabel, subFrame3Canvas1, subFrame3Canvas2, trendShort, changeImpShort, predictShort,
                    relatedShort, trendLong, changeImpLong, predictLong, relatedLong
                ]
            )
        )
        showSpecAnBt.place(relx=0.75, rely=0.5, anchor=CENTER)

        # subframe2 contents

        # parameters
        canvas_title_font = 'Calibri 20'
        canvas_axis_font = 'Calibri 13'
        canvas_font = 'Calibri 10'

        title_yoffset = 35

        legend_width = 30
        legend_xpad = 10
        legend_ypad = 30
        legend_labelpad = 40

        axis_end_padding = 30
        axis_side_padding = 30
        x_label_xoffset = 45
        x_label_yoffset = 15
        y_label_xoffset = 10
        '''CHANGE THIS TO HIGHLIGHT_POSITION AND HIGHLIGHT_HEIGHT'''
        highlight_position = 50
        highlight_height = 70

        y_axis_offset = 20
        graph_top_start = 70
        graph_bottom_padding = 10
        highlight_width = 100

        # colorplot
        global subdiv_num, color
        subdiv_num = 255
        rgb_s = [0, 0, 0]
        rgb_e = [0, 255, 255]
        inc = [(v1 - v2) / subdiv_num for v1, v2 in zip(rgb_e, rgb_s)]
        color = [
            f"#{int(rgb_s[0] + (i * inc[0])):02x}{int(rgb_s[1] + (i * inc[1])):02x}{int(rgb_s[2] + (i * inc[2])):02x}"
            for i in range(subdiv_num + 1)]

        # canvas
        subFrame2Canvas = Canvas(subFrame2, height=gui_height, width=frame_widths[1], bg='#E2E2E2')
        subFrame2Canvas.grid(row=0, column=0)
        subFrame2Canvas.update()
        self.__subFrame2CanvasInit(
            subFrame2Canvas, [
                canvas_title_font, canvas_axis_font, canvas_font, title_yoffset, legend_width, legend_xpad,
                legend_ypad,
                legend_labelpad, axis_end_padding, axis_side_padding, x_label_xoffset, x_label_yoffset,
                y_label_xoffset,
                highlight_position, highlight_height, y_axis_offset, graph_top_start, graph_bottom_padding,
                highlight_width
            ]
        )

        # subframe 3 contents

        # parameters
        side_padding = 10
        price_padding = 10

        canvas_height = 250
        canvas_x_offset = 3
        canvas_width = frame_widths[2] - side_padding * 2 + canvas_x_offset * 2
        canvas_bd_type = SUNKEN

        text_height1 = 120
        text_height2 = 50
        text_padding = 20

        # widgets
        subFrame3.config(padx=side_padding)

        priceLabel = Label(subFrame3, text=f"Current Price:", font=default_font, pady=price_padding)
        priceLabel.grid(row=0, column=0, sticky=W)

        subFrame3Canvas1 = Canvas(
            subFrame3, height=canvas_height, width=canvas_width, bg='#E2E2E2', relief=canvas_bd_type)
        subFrame3Canvas1.grid(row=1, column=0)

        subFrame3TextFrame1 = Frame(subFrame3, height=text_height1 + text_height2,
                                    width=frame_widths[2] - side_padding)
        subFrame3TextFrame1.grid(row=2, column=0)
        subFrame3TextFrame1.grid_propagate(False)

        subFrame3TextFrame1Center = Frame(
            subFrame3TextFrame1, height=text_height1 + text_height2, width=frame_widths[2] - side_padding)
        subFrame3TextFrame1Center.place(relx=0, rely=0.5, anchor=W)

        subFrame3Canvas2 = Canvas(
            subFrame3, height=canvas_height, width=canvas_width, bg='#E2E2E2', relief=canvas_bd_type)
        subFrame3Canvas2.grid(row=4, column=0)

        subFrame3TextFrame2 = Frame(subFrame3, height=text_height1 + text_height2,
                                    width=frame_widths[2] - side_padding)
        subFrame3TextFrame2.grid(row=5, column=0)
        subFrame3TextFrame2.grid_propagate(False)

        subFrame3TextFrame2Center = Frame(
            subFrame3TextFrame2, height=text_height1 + text_height2, width=frame_widths[2] - side_padding)
        subFrame3TextFrame2Center.place(relx=0, rely=0.5, anchor=W)

        # label text
        Label(
            subFrame3TextFrame1Center, text=f"Short-Term ({self.timePeriod[0][0]}, {self.timePeriod[0][1]}): ",
            font=default_font).grid(row=0, column=0, sticky=W, padx=text_padding)
        Label(subFrame3TextFrame1Center, text="Change Importance: ", font=default_font).grid(
            row=1, column=0, sticky=W, padx=text_padding)
        Label(subFrame3TextFrame1Center, text="Short-Term Prediction: ", font=default_font).grid(
            row=2, column=0, sticky=W, padx=text_padding)
        Label(subFrame3TextFrame1Center, text="Mainly Related Stocks: ", font=default_font).grid(
            row=3, column=0, sticky=W, padx=text_padding)

        Label(
            subFrame3TextFrame2Center, text=f"Long-Term ({self.timePeriod[1][0]}, {self.timePeriod[1][1]}): ",
            font=default_font).grid(row=0, column=0, sticky=W, padx=text_padding)
        Label(subFrame3TextFrame2Center, text="Change Importance: ", font=default_font).grid(
            row=1, column=0, sticky=W, padx=text_padding)
        Label(subFrame3TextFrame2Center, text="Long-Term Prediction: ", font=default_font).grid(
            row=2, column=0, sticky=W, padx=text_padding)
        Label(subFrame3TextFrame2Center, text="Mainly Related Stocks: ", font=default_font).grid(
            row=3, column=0, sticky=W, padx=text_padding)

        # text widgets
        trendShort = Label(subFrame3TextFrame1Center, text="", font=default_font)
        trendShort.grid(row=0, column=1, sticky=W)

        changeImpShort = Label(subFrame3TextFrame1Center, text="", font=default_font)
        changeImpShort.grid(row=1, column=1, sticky=W)

        predictShort = Label(subFrame3TextFrame1Center, text="", font=default_font)
        predictShort.grid(row=2, column=1, sticky=W)

        relatedShort = Label(subFrame3TextFrame1Center, text="", font=default_font, justify=LEFT)
        relatedShort.grid(row=3, column=1, sticky=W)

        trendLong = Label(subFrame3TextFrame2Center, text="", font=default_font)
        trendLong.grid(row=0, column=1, sticky=W)

        changeImpLong = Label(subFrame3TextFrame2Center, text="", font=default_font)
        changeImpLong.grid(row=1, column=1, sticky=W)

        predictLong = Label(subFrame3TextFrame2Center, text="", font=default_font)
        predictLong.grid(row=2, column=1, sticky=W)

        relatedLong = Label(subFrame3TextFrame2Center, text="", font=default_font, justify=LEFT)
        relatedLong.grid(row=3, column=1, sticky=W)

        root.mainloop()

    def __bound_to_mousewheel(self, event, canvas: Canvas):
        """
        Helper event method for self.runStockGUI() method.
        Binds scrollwheel to canvas in Frame1 for scrolling when mouse enters canvas widget.
        Calls this.__on_mousewheel() when mousewheel event is detected.

        :param event: Tkinter event argument for entering
        :param canvas: Tkinter canvas object
        :return: None
        """
        canvas.bind_all("<MouseWheel>", lambda event: self.__on_mousewheel(event, canvas))

    def __unbound_to_mousewheel(self, event, canvas: Canvas):
        """
        Helper event method for self.runStockGUI() method.
        Unbinds scrollwheel to canvas when mouse leaves canvas widget.

        :param event: Tkinter event argument for leaving
        :param canvas: Tkinter canvas object
        :return: None
        """
        canvas.unbind_all("<MouseWheel>")

    def __on_mousewheel(self, event, canvas: Canvas):
        """
        Helper event method for self.__bound_to_mousewheel() method.
        Scrolls canvas based on mousewheel movement.

        :param event: Tkinter event argument for mousewheel
        :param canvas: Tkinter canvas object
        :return: None
        """
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def __displayResults(self) -> None:
        """
        Sub method for self.runStockGUI.
        Creates Toplevel to display company relation results in diagram form using TKinter.
        User can select two companies to visually see keyword relations in graph form.

        :return: None
        """
        # data
        stockRelData = []
        for i in range(0, len(self.allStockList) - 1):
            for j in range(i + 1, len(self.allStockList)):
                com1 = self.allStockList[i].companyName
                com2 = self.allStockList[j].companyName
                query = f"{com1}, {com2}"
                self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")
                stockRelData.append(float(self.cur.fetchone()[0]))

        # parameters
        canvas_width = 1000
        canvas_height = 950
        button_height = 50

        result_width = 800
        result_height = 800

        item_radius = 450
        oval_width = 50
        oval_height = 40
        oval_line_width = 2
        line_width = 1
        oval_color = "#C4E1FE"

        # elements
        relResultWindow = Toplevel()
        relResultWindow.bind("<Escape>", lambda event: self.__destroyToplevel(event, relResultWindow))
        relResultWindow.title("Stock Company Analysis Results")
        relResultWindow.grid_rowconfigure(0, weight=1)
        relResultWindow.grid_columnconfigure(0, weight=1)

        allFrame = Frame(relResultWindow)
        allFrame.grid(row=0, column=0, padx=0, pady=20)

        # canvas half
        canvasFrame = Frame(allFrame, padx=5, pady=5)
        canvasFrame.grid(row=0, column=0)

        displayCanvas = Canvas(canvasFrame, width=canvas_width, height=canvas_height)
        displayCanvas.grid(row=0, column=0)

        buttonFrame = Frame(allFrame, width=canvas_width, height=button_height)
        buttonFrame.grid(row=1, column=0)

        com_options = [self.allStockList[i].companyName for i in range(len(self.allStockList))]

        com1 = StringVar()
        com1.set("Select a Company (1)")
        option1Drop = OptionMenu(buttonFrame, com1, *com_options)
        option1Drop.config(width=20)
        option1Drop.grid(row=0, column=0)

        com2 = StringVar()
        com2.set("Select a Company (2)")
        option2Drop = OptionMenu(buttonFrame, com2, *com_options)
        option2Drop.config(width=20)
        option2Drop.grid(row=0, column=1)

        resultButton = Button(
            buttonFrame, text="Display Correlation Graph", width=20, command=lambda: self.__updateResultToplevel(
                relResultWindow, com1, com2, [
                    positions, boldItems, oval_width, oval_height, oval_color, displayCanvas, fig, resultCanvas
                ]))
        resultButton.grid(row=0, column=2)

        # items
        positions = []
        colorLines = []
        boldItems = []
        stockOvals = []

        center_xy = [canvas_width // 2, canvas_height // 2]
        for i in range(len(self.allStockList)):
            new_x = sin(2 * pi / len(self.allStockList) * i) * item_radius
            new_y = -cos(2 * pi / len(self.allStockList) * i) * item_radius
            positions.append([center_xy[0] + new_x, center_xy[1] + new_y])

        idx = 0
        for i in range(0, len(self.allStockList) - 1):
            for j in range(i + 1, len(self.allStockList)):
                colorLines.append(self.__drawColorLine(
                    positions[i][0], positions[i][1],
                    positions[j][0], positions[j][1],
                    displayCanvas, line_width, stockRelData[idx]))
                idx += 1

        # draw ovals
        for pos in positions:
            stockOvals.append(
                displayCanvas.create_oval(
                    pos[0] - oval_width // 2,
                    pos[1] - oval_height // 2,
                    pos[0] + oval_width // 2,
                    pos[1] + oval_height // 2,
                    width=oval_line_width, fill=oval_color)
            )

        # draw stock labels
        for i in range(len(self.allStockList)):
            displayCanvas.create_text(positions[i][0], positions[i][1], text=self.allStockList[i].companyName[:2])

        # result half
        resultFrame = Frame(allFrame, padx=25, pady=5)
        resultFrame.grid(row=0, column=1)

        fig = plt.figure()
        resultCanvas = FigureCanvasTkAgg(fig, master=resultFrame)
        resultCanvas.get_tk_widget().config(width=result_width, height=result_height)
        resultCanvas.get_tk_widget().pack(fill=BOTH, expand=True)
        # resultCanvas.draw()

        relResultWindow.mainloop()

    def __drawColorLine(self, x1, y1, x2, y2, canvas, line_width, dataValue) -> list:
        """
        Helper method for self.__displayResults() and self.__updateResultToplevel().
        Draws colored line on given canvas based on coordinates and given data value.
        Color is chosen based on global color/subdiv_num/maxRelSCore/minRelScore variables.

        :param x1: first x-coordinate
        :param y1: first y-coordinate
        :param x2: second x-coordinate
        :param y2: second y-coordinate
        :param canvas: given Canvas Tkinter widget
        :param line_width: given line width
        :param dataValue: dataValue to compare to max/minRelScore
        :return: canvas line object
        """
        color_idx = int((dataValue - minRelScore) / (maxRelScore - minRelScore) * subdiv_num)
        return canvas.create_line(x1, y1, x2, y2, fill=color[color_idx], width=line_width)

    def __updateResultToplevel(self, toplevel: Toplevel, com1: StringVar, com2: StringVar,
                               given_items: list) -> None:
        """
        Sub method for self.__displayResults method.
        Updates Matplotlib Canvas Figure to display keyword relations for selected companies in 3d graph form.

        :param stockVars: List of Stock objects (companies) selected in Tkinter GUI
        :param fig: Matplotlib figure containing FigureCanvasTkAgg subplot
        :param resultCanvas: FigureCanvasTkAgg object to be updated
        :return: None
        """
        [positions, boldItems, oval_width, oval_height, oval_color, displayCanvas, fig, resultCanvas] = given_items

        # refresh everything
        for item in boldItems:
            displayCanvas.delete(item)
        boldItems.clear()
        fig.clf()

        # variable lists
        selectStocks = []
        selectIdx = []

        for i in range(len(self.allStockList)):
            if com1.get() == self.allStockList[i].companyName or com2.get() == self.allStockList[i].companyName:
                selectStocks.append(self.allStockList[i])
                selectIdx.append(i)

        if len(selectStocks) != 2:
            return

        # print keywords
        stock1 = selectStocks[0]
        stock2 = selectStocks[1]

        self.cur.execute(f"select * from Companies where Name = \'{stock1.companyName}\'")
        result = self.cur.fetchone()
        print(f"{stock1.companyName}: {result[1]}")

        self.cur.execute(f"select * from Companies where Name = \'{stock2.companyName}\'")
        result = self.cur.fetchone()
        print(f"{stock2.companyName}: {result[1]}")

        # update right figure plot
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.clear()
        ax.set_xticks([i for i in range(self.keyword_cnt + 1)])
        ax.set_yticks([i for i in range(self.keyword_cnt + 1)])
        ax.set_zticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax.set_zlim(-0.2, 1.0)

        # prepare data
        stock1 = selectStocks[0]
        stock2 = selectStocks[1]
        companies = f"{stock1.companyName}, {stock2.companyName}"

        self.cur.execute(f"select * from Relations where Companies = \'{companies}\'")
        result = self.cur.fetchone()

        relScore = float(result[2])
        temp = list(map(float, result[1].split(", ")))
        keywordRel = []
        for i in range(self.keyword_cnt):
            keywordRel.append(temp[self.keyword_cnt * i: self.keyword_cnt * (i + 1)])

        # update figure axes
        ax.set_title(f"{stock1.companyName} and {stock2.companyName}: {relScore:.1f}")

        x, y, z = [], [], []
        dx, dy, dz = [], [], []
        for i in range(self.keyword_cnt):
            for j in range(self.keyword_cnt):
                x.append(i)
                y.append(j)
                z.append(0)
                dx.append(1)
                dy.append(1)
                dz.append(keywordRel[i][j])

        dz_np = np.array(dz)
        dz_np = np.squeeze(dz_np)

        nrm = mpl.colors.Normalize(-1, 1)
        colors = plt.cm.RdBu(nrm(-dz_np))
        alpha = np.linspace(0.2, 0.95, self.keyword_cnt, endpoint=True)

        for i in range(len(x)):
            ax.bar3d(
                x[i], y[i], z[i], dx[i], dy[i], dz[i],
                alpha=alpha[i % self.keyword_cnt], color=colors[i], linewidth=0)
        resultCanvas.draw()

        # update left diagram

        # parameters
        hl_line_width = 7
        oval_hl_line_width = 5
        oval_outline = 'red'

        # relation data
        query = f"{selectStocks[0].companyName}, {selectStocks[1].companyName}"
        self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")
        dataValue = float(self.cur.fetchone()[0])

        # repeat for animation
        animation_cnt = 40

        for cnt in range(animation_cnt + 1):
            # clear bolded items
            for item in boldItems:
                displayCanvas.delete(item)
            boldItems.clear()

            # redraw
            total_perc = sqrt(1 - ((cnt - animation_cnt) ** 2 / (animation_cnt ** 2)))

            # draw bolded color line
            idx1 = selectIdx[0]
            idx2 = selectIdx[1]

            # line pos calculation
            mid_pos = [(positions[idx1][0] + positions[idx2][0]) / 2, (positions[idx1][1] + positions[idx2][1]) / 2]
            line1_pos = [[positions[idx1][0], positions[idx1][1]], [
                total_perc * mid_pos[0] + (1 - total_perc) * positions[idx1][0],
                total_perc * mid_pos[1] + (1 - total_perc) * positions[idx1][1]
            ]]
            line2_pos = [[positions[idx2][0], positions[idx2][1]], [
                total_perc * mid_pos[0] + (1 - total_perc) * positions[idx2][0],
                total_perc * mid_pos[1] + (1 - total_perc) * positions[idx2][1]
            ]]
            # stock 1 line
            boldItems.append(self.__drawColorLine(
                line1_pos[0][0], line1_pos[0][1], line1_pos[1][0], line1_pos[1][1],
                displayCanvas, hl_line_width * total_perc, dataValue))
            # stock 2 line
            boldItems.append(self.__drawColorLine(
                line2_pos[0][0], line2_pos[0][1], line2_pos[1][0], line2_pos[1][1],
                displayCanvas, hl_line_width * total_perc, dataValue))

            # redraw ovals & stock labels
            for idx in [idx1, idx2]:
                boldItems.append(displayCanvas.create_oval(
                    positions[idx][0] - oval_width // 2,
                    positions[idx][1] - oval_height // 2,
                    positions[idx][0] + oval_width // 2,
                    positions[idx][1] + oval_height // 2,
                    width=oval_hl_line_width * total_perc, outline=oval_outline, fill=oval_color))
                boldItems.append(displayCanvas.create_text(
                    positions[idx][0], positions[idx][1], text=self.allStockList[idx].companyName[:2]))

            toplevel.update()
            sleep(0.01)

    def __destroyToplevel(self, event, window: Toplevel) -> None:
        """
        Sub method for self.__displayResults method.
        Event method to destroy current Toplevel.

        :param event: Tkinter event
        :param window: Tkinter Toplevel object
        :return: None
        """
        window.destroy()

    def __displaySpecificResults(self, main_idx: int, subFrame2Args: list,
                                 subFrame3Args: list) -> None:  # idx: base 1
        """
        Helper method for self.__runStockGUI() method.
        Calls updates on subFrame3 and subFrame2 (in that order).

        :param main_idx: Stock Radiobutton IntVar() value
        :param subFrame2Args: arguments for updating subFrame2
        :param subFrame3Args: arguments for updating subFrame3
        :return: None
        """
        # updates subFrame2 and subFrame3

        # subFrame 3
        self.__updateSubFrame3(main_idx, subFrame3Args)

        # subFrame 2
        [subFrame2Canvas, parameters, stock_inc] = subFrame2Args
        self.__updateSubFrame2(subFrame2Canvas, parameters, stock_inc, main_idx)

    def __subFrame2CanvasInit(self, subFrame2Canvas: Canvas, parameters: list) -> None:
        """
        Helper method for self.stockGUI() method.
        Initializes subFrame2 canvas before use.

        :param subFrame2Canvas: subFrame2 canvas Tkinter widget
        :param parameters: parameters for subFrame2
        :return: None
        """
        [canvas_title_font, canvas_axis_font, canvas_font, title_yoffset, legend_width, legend_xpad, legend_ypad,
         legend_labelpad, axis_end_padding, axis_side_padding, x_label_xoffset, x_label_yoffset, y_label_xoffset,
         highlight_position, highlight_height, y_axis_offset, graph_top_start, graph_bottom_padding,
         highlight_width] = parameters

        canvas_height = subFrame2Canvas.winfo_height()
        canvas_width = subFrame2Canvas.winfo_width()

        min_graph_height = graph_top_start
        max_graph_height = canvas_height - axis_end_padding - graph_bottom_padding
        min_graph_width = (legend_xpad * 2 + legend_width + legend_labelpad)
        max_graph_width = canvas_width - axis_end_padding

        tick_length = 10
        line_width = 2

        # legend
        for i in range(max_graph_height - min_graph_height + 1):
            ypos = min_graph_height + i
            left_xpos = legend_labelpad + legend_xpad
            right_xpos = left_xpos + legend_width
            color_idx = int((max_graph_height - ypos) / (max_graph_height - min_graph_height) * subdiv_num)
            subFrame2Canvas.create_line(left_xpos, ypos, right_xpos, ypos, fill=color[color_idx], width=1)
        subFrame2Canvas.create_rectangle(
            legend_labelpad + legend_xpad, min_graph_height,
            legend_labelpad + legend_xpad + legend_width, max_graph_height, width=2)

        # legend label
        subFrame2Canvas.create_text(
            legend_labelpad - y_label_xoffset, (min_graph_height + max_graph_height) / 2,
            text="Similarity", font=canvas_axis_font, angle=90)
        subFrame2Canvas.create_text(
            legend_labelpad - y_label_xoffset, min_graph_height + axis_end_padding,
            text="Max", font=canvas_axis_font, angle=90)
        subFrame2Canvas.create_text(
            legend_labelpad - y_label_xoffset, max_graph_height - axis_end_padding,
            text="Min", font=canvas_axis_font, angle=90)

        # y axis
        subFrame2Canvas.create_line(
            (min_graph_width + max_graph_width) / 2, title_yoffset + axis_end_padding,
            (min_graph_width + max_graph_width) / 2, max_graph_height - highlight_position - (highlight_height / 2),
            dash=(3, 5), fill='black', width=2)

        # x axis
        subFrame2Canvas.create_line(
            min_graph_width, max_graph_height,
            max_graph_width, max_graph_height,
            fill='black', width=line_width)
        # x axis tick
        subFrame2Canvas.create_line(
            (min_graph_width + max_graph_width) / 2, max_graph_height - tick_length / 2,
            (min_graph_width + max_graph_width) / 2, max_graph_height + tick_length / 2,
            fill='black', width=line_width)

        # x axis label
        subFrame2Canvas.create_text(
            (min_graph_width + max_graph_width) / 2, max_graph_height + x_label_yoffset,
            text="Increase (%)", font=canvas_axis_font)
        subFrame2Canvas.create_text(
            max_graph_width + axis_end_padding - x_label_xoffset, max_graph_height + x_label_yoffset,
            text="+ (%)", font=canvas_axis_font)
        subFrame2Canvas.create_text(
            min_graph_width + x_label_xoffset, max_graph_height + x_label_yoffset,
            text="- (%)", font=canvas_axis_font)

        # highlight rectangle
        subFrame2Canvas.create_rectangle(
            (min_graph_width + max_graph_width) / 2 - highlight_width,
            max_graph_height - highlight_position - highlight_height / 2,
            (min_graph_width + max_graph_width) / 2 + highlight_width,
            max_graph_height - highlight_position + highlight_height / 2,
            fill='white', width=0)

    def __updateSubFrame2(self, subFrame2Canvas: Canvas, parameters: list, stock_inc: list, main_idx: int) -> None:
        """
        Helper method for self.__displaySpecificResults() method.
        Updates subFrame2 canvas based on given parameter values.

        :param subFrame2Canvas: subFrame2 canvas Tkinter widget
        :param parameters: parameters for subFrame2
        :param stock_inc: stock increase value in percentage
        :param main_idx: stock Radiobutton IntVar() value
        :return: None
        """
        if main_idx == 0:
            return

        # unpack arguments
        [canvas_title_font, canvas_axis_font, canvas_font, title_yoffset, legend_width, legend_xpad, legend_ypad,
         legend_labelpad, axis_end_padding, axis_side_padding, x_label_xoffset, x_label_yoffset, y_label_xoffset,
         highlight_position, highlight_height, y_axis_offset, graph_top_start, graph_bottom_padding,
         highlight_width] = parameters

        # reset canvas
        subFrame2Canvas.delete('all')
        self.__subFrame2CanvasInit(subFrame2Canvas, parameters)

        # data
        stockRelData = []

        query = f"{self.allStockList[0].companyName}, {self.allStockList[1].companyName}"
        self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")

        for i in range(len(self.allStockList)):
            for j in range(len(self.allStockList)):
                if i != j:
                    com1 = self.allStockList[i].companyName
                    com2 = self.allStockList[j].companyName
                    query = f"{com1}, {com2}"
                    self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")
                    result = float(self.cur.fetchone()[0])

                    if i == main_idx - 1:
                        stockRelData.append(result)

        maxInc = minInc = self.allStockList[0].stockChangeDataShort[0] / self.allStockList[0].stockDataShort[
            0] * 100
        for i in range(len(self.allStockList)):
            percs = [
                self.allStockList[i].stockChangeDataShort[j] / self.allStockList[i].stockDataShort[j] * 100
                for j in range(len(self.allStockList[i].stockChangeDataShort))]
            maxInc = max(maxInc, max(percs))
            minInc = min(minInc, min(percs))

        # parameters
        box_line_width = 4
        box_width = 15
        box_length = 15
        box_ypad = 10
        box_xpad = 20

        # items
        positions = []  # [[left x_perc, right x_perc, cur x_perc], y_cnt, color_idx], ...
        final_positions = []  # [[left x_coor, right x_coor, cur x_coor], y_coor, color_hex], ...
        stockBoxes = []

        # get positions
        canvas_height = subFrame2Canvas.winfo_height()
        canvas_width = subFrame2Canvas.winfo_width()

        min_graph_height = graph_top_start + box_ypad
        max_graph_height = \
            canvas_height - axis_end_padding - graph_bottom_padding - highlight_position \
            - (highlight_height / 2) - box_ypad
        min_graph_width = (legend_xpad * 2 + legend_width + legend_labelpad) + box_xpad
        max_graph_width = canvas_width - axis_end_padding - box_xpad

        # label main stock
        subFrame2Canvas.create_text(
            (min_graph_width + max_graph_width) / 2, title_yoffset,
            text=f"{self.allStockList[main_idx - 1].companyName}", font=canvas_title_font)

        # repeat for animation
        animation_cnt = 40

        for cnt in range(animation_cnt + 1):
            for item in stockBoxes:
                for item2 in item:
                    subFrame2Canvas.delete(item2)
            positions.clear()
            final_positions.clear()
            stockBoxes.clear()

            total_perc = sqrt(1 - ((cnt - animation_cnt) ** 2 / (animation_cnt ** 2)))

            # calculate position (perc)
            for i in range(len(self.allStockList)):
                if i != main_idx - 1:
                    idx = i - (i > main_idx - 1)
                    color_idx = int((stockRelData[idx] - minRelScore) / (maxRelScore - minRelScore) * subdiv_num)

                    change_data = [
                        self.allStockList[i].stockChangeDataShort[j] / self.allStockList[i].stockDataShort[j] * 100
                        for j in range(len(self.allStockList[i].stockChangeDataShort))]
                    left_xperc = min(change_data) / max(abs(maxInc), abs(minInc))
                    right_xperc = max(change_data) / max(abs(maxInc), abs(minInc))
                    cur_xperc = stock_inc[i] / max(abs(maxInc), abs(minInc))

                    # multiply animation perc
                    perc_list = [left_xperc, right_xperc, cur_xperc]
                    for j in range(len(perc_list)):
                        perc_list[j] *= total_perc

                    positions.append([perc_list, idx, color_idx])

            # calculate final positions
            for pos in positions:
                left_xpos = \
                    (max_graph_width + min_graph_width) / 2 \
                    + (max_graph_width - min_graph_width) / 2 * pos[0][0]
                right_xpos = \
                    (max_graph_width + min_graph_width) / 2 \
                    + (max_graph_width - min_graph_width) / 2 * pos[0][1]
                cur_xpos = \
                    (max_graph_width + min_graph_width) / 2 \
                    + (max_graph_width - min_graph_width) / 2 * pos[0][2]

                y_pos = min_graph_height + (max_graph_height - min_graph_height - box_width) \
                        / (len(self.allStockList) - 2) * pos[1]
                color_hex = color[pos[2]]
                final_positions.append([[left_xpos, right_xpos, cur_xpos], y_pos, color_hex])

            # draw boxes
            for i in range(len(final_positions)):  # [[left x_coor, right x_coor, cur x_coor], y_coor, color_hex]
                pos = final_positions[i]
                stock_idx = i + (i >= main_idx - 1)
                tag = f"box{stock_idx}"

                center_oval = subFrame2Canvas.create_oval(
                    pos[0][2] - box_length / 2, pos[1] - box_width / 2,
                    pos[0][2] + box_length / 2, pos[1] + box_width / 2,
                    width=0, fill=pos[2], tags=tag
                )
                center_line = subFrame2Canvas.create_line(
                    pos[0][0], pos[1],
                    pos[0][1], pos[1],
                    width=box_line_width, fill=pos[2], tags=tag
                )
                left_line = subFrame2Canvas.create_line(
                    pos[0][0], pos[1] - box_width / 2,
                    pos[0][0], pos[1] + box_width / 2,
                    width=box_line_width, fill=pos[2]
                )
                right_line = subFrame2Canvas.create_line(
                    pos[0][1], pos[1] - box_width / 2,
                    pos[0][1], pos[1] + box_width / 2,
                    width=box_line_width, fill=pos[2]
                )
                stockBoxes.append([center_oval, center_line, left_line, right_line])
            root.update()
            sleep(0.01)

        # bind tk.ACTIVE with function to update display function
        for i in range(len(final_positions)):  # [[left x_coor, right x_coor, cur x_coor], y_coor, color_hex]
            stock_idx = i + (i >= main_idx - 1)
            tag = f"box{stock_idx}"
            param = stockRelData, box_line_width, box_width, box_length, box_ypad, box_xpad, min_graph_height, max_graph_height, min_graph_width, max_graph_width, highlight_position, highlight_height, canvas_axis_font
            subFrame2Canvas.tag_bind(
                tag, "<Enter>",
                lambda event, canvas=subFrame2Canvas, stock_idx=stock_idx, rel_idx=i, tag=tag, parameters=param:
                self.__subFrame2SpecificDisplay(canvas, stock_idx, rel_idx, tag, parameters))
            subFrame2Canvas.bind(
                "<Button-1>",
                lambda event, canvas=subFrame2Canvas:
                canvas.delete("highlight"))

    def __subFrame2SpecificDisplay(self, canvas: Canvas, stock_idx: int, rel_idx: int, tag: str, parameters: list):
        """
        Helper method for self.__updateSubFrame2() method.
        Updates highlight related objects in subFrame2 canvas.

        :param canvas: subFrame2 canvas
        :param stock_idx: stock index based on self.allStockList
        :param rel_idx: relative stock index excluding currently selected stock
        :param tag: canvas tagID for highlight related items
        :param parameters: relevant parameter list
        :return: None
        """
        [stockRelData, box_line_width, box_width, box_length, box_ypad, box_xpad, min_height, max_height, min_width,
         max_width, highlight_position, highlight_height, canvas_axis_font] = parameters
        canvas.delete("highlight")

        increase = \
            self.allStockList[stock_idx].stockChangeDataShort[-1] / \
            self.allStockList[stock_idx].stockDataShort[-2] * 100
        similarity = stockRelData[rel_idx]

        items = canvas.find_withtag(tag)
        bounds = list(zip(*[canvas.bbox(items[j]) for j in range(len(items))]))
        canvas.create_rectangle(
            min(bounds[0]), min(bounds[1]),
            max(bounds[2]), max(bounds[3]),
            width=2, outline="red", tags="highlight"
        )

        canvas.create_text(
            (max_width + min_width) / 2, max_height + highlight_height / 2 + box_ypad,
            text=f"Selected: {self.allStockList[stock_idx].companyName}\n"
                 f"Increase: {increase: .2f}%\n"
                 f"Similarity: {similarity: .2f}",
            fill="red", tags="highlight", font=canvas_axis_font, justify=CENTER
        )

    def __updateSubFrame3(self, main_idx: int, widgets: list) -> None:
        """
        Helper method for self.__displaySpecificResults() method.
        Updates subFrame3 based on given widget/parameter values.

        :param main_idx: stock index based on self.allStockList
        :param widgets: relevant widgets/parameters for subFrame3
        :return: None
        """

        if main_idx == 0:
            return

        # unpack arguments
        [priceLabel, subFrame3Canvas1, subFrame3Canvas2, trendShort, changeImpShort, predictShort, relatedShort,
         trendLong, changeImpLong, predictLong, relatedLong] = widgets

        # other parameters
        company_cnt = 6

        # reset both canvases
        subFrame3Canvas1.delete('all')
        subFrame3Canvas2.delete('all')

        # find stock
        curStock = self.allStockList[main_idx - 1]

        # update price
        priceLabel.config(text=f"Current Price: {curStock.stockDataShort[-1]:.2f} USD")

        # canvas parameters
        canvas_width = subFrame3Canvas1.winfo_width()
        canvas_height = subFrame3Canvas1.winfo_height()

        point_pad = 20
        axis_pad = 40
        axis_width = 1
        y_pad = 5
        axis_fill = 'black'

        grid_width = 1
        grid_fill = '#BFBFBF'

        tick_length = 5
        tick_width = 1
        tick_fill = 'black'
        text_size = 10

        line_width = 3
        line_fill = '#33D4FF'
        oval_size = 5

        intervals = [100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1]
        grid_cnt = 5

        # canvas 1 data
        short_minval = min(curStock.stockDataShort)
        short_maxval = max(curStock.stockDataShort)

        short_interval_values = list()
        short_interval_raw = list()
        short_interval = 0
        short_points_raw = list()

        for inter in intervals:
            if (short_maxval - short_minval) / inter >= grid_cnt:
                short_interval = inter
                break

        if short_interval == 0:
            short_interval = intervals[-1]

        int_min = ceil(short_minval / short_interval) * short_interval
        int_max = floor(short_maxval / short_interval) * short_interval

        int_it = int_min
        while int_it <= int_max:
            short_interval_values.append(int_it)
            int_it += short_interval

        for val in short_interval_values:
            short_interval_raw.append(self.__findCanvasYPos(
                subFrame3Canvas1, y_pad, short_minval, short_maxval, val))

        for i in range(len(curStock.stockDataShort)):
            short_points_raw.append(self.__findCanvasPos(
                subFrame3Canvas1, point_pad + axis_pad, y_pad, len(curStock.stockDataShort), short_minval,
                short_maxval,
                i, curStock.stockDataShort[i]))

        # draw canvas 1
        subFrame3Canvas1.create_line(
            canvas_width - axis_pad, 0,
            canvas_width - axis_pad, canvas_height,
            fill=axis_fill, width=axis_width)

        for i in range(len(short_interval_values)):
            val = short_interval_values[i]
            raw_val = short_interval_raw[i]

            subFrame3Canvas1.create_line(
                0, raw_val,
                canvas_width - axis_pad, raw_val,
                fill=grid_fill, width=grid_width)
            subFrame3Canvas1.create_line(
                canvas_width - axis_pad, raw_val,
                canvas_width - axis_pad + tick_length, raw_val,
                fill=tick_fill, width=tick_width)
            subFrame3Canvas1.create_text(
                canvas_width - axis_pad + point_pad, raw_val,
                text=f"{val:.0f}")

        for i in range(len(short_points_raw) - 1):
            subFrame3Canvas1.create_line(
                short_points_raw[i][0], short_points_raw[i][1],
                short_points_raw[i + 1][0], short_points_raw[i + 1][1],
                fill=line_fill, width=line_width)
        subFrame3Canvas1.create_oval(
            short_points_raw[-1][0] - oval_size, short_points_raw[-1][1] - oval_size,
            short_points_raw[-1][0] + oval_size, short_points_raw[-1][1] + oval_size,
            fill=line_fill, width=0)

        # canvas 1 data

        long_minval = min(curStock.stockDataLong)
        long_maxval = max(curStock.stockDataLong)

        long_interval_values = list()
        long_interval_raw = list()
        long_interval = 0
        long_points_raw = list()

        for inter in intervals:
            if (long_maxval - long_minval) / inter >= grid_cnt:
                long_interval = inter
                break

        if long_interval == 0:
            long_interval = intervals[-1]

        int_min = ceil(long_minval / long_interval) * long_interval
        int_max = floor(long_maxval / long_interval) * long_interval

        int_it = int_min
        while int_it <= int_max:
            long_interval_values.append(int_it)
            int_it += long_interval

        for val in long_interval_values:
            long_interval_raw.append(self.__findCanvasYPos(
                subFrame3Canvas2, y_pad, long_minval, long_maxval, val))

        for i in range(len(curStock.stockDataLong)):
            long_points_raw.append(self.__findCanvasPos(
                subFrame3Canvas2, point_pad + axis_pad, y_pad, len(curStock.stockDataLong), long_minval,
                long_maxval,
                i, curStock.stockDataLong[i]))

        # draw canvas 2
        subFrame3Canvas2.create_line(
            canvas_width - axis_pad, 0,
            canvas_width - axis_pad, canvas_height,
            fill=axis_fill, width=axis_width)

        for i in range(len(long_interval_values)):
            val = long_interval_values[i]
            raw_val = long_interval_raw[i]

            subFrame3Canvas2.create_line(
                0, raw_val,
                canvas_width - axis_pad, raw_val,
                fill=grid_fill, width=grid_width)
            subFrame3Canvas2.create_line(
                canvas_width - axis_pad, raw_val,
                canvas_width - axis_pad + tick_length, raw_val,
                fill=tick_fill, width=tick_width)
            subFrame3Canvas2.create_text(
                canvas_width - axis_pad + point_pad, raw_val,
                text=f"{val:.0f}")

        for i in range(len(long_points_raw) - 1):
            subFrame3Canvas2.create_line(
                long_points_raw[i][0], long_points_raw[i][1],
                long_points_raw[i + 1][0], long_points_raw[i + 1][1],
                fill=line_fill, width=line_width)
        subFrame3Canvas2.create_oval(
            long_points_raw[-1][0] - oval_size, long_points_raw[-1][1] - oval_size,
            long_points_raw[-1][0] + oval_size, long_points_raw[-1][1] + oval_size,
            fill=line_fill, width=0)

        predictionResults = self.__calculatePrediction(
            curStock)  # [(short-term, percent, [stocks]), (long-term, percent, [stocks])]

        # update short info
        trendShortPercent = curStock.stockChangeDataShort[-1] / curStock.stockDataShort[-2] * 100
        if curStock.stockChangeDataShort[-1] >= 0:
            trendShortColor = 'green'
            trendShortText = f'+{curStock.stockChangeDataShort[-1]: .2f} USD (+{trendShortPercent: .2f}%)'
        else:
            trendShortColor = 'red'
            trendShortText = f'{curStock.stockChangeDataShort[-1]: .2f} USD ({trendShortPercent: .2f}%)'

        if curStock.changeImportance[0]:
            changeImpShortColor = 'green'
        else:
            changeImpShortColor = 'red'

        if predictionResults[0][0] >= 0:
            predictShortText = f"+{predictionResults[0][0]: .2f} USD (+{predictionResults[0][1]: .2f}%)"
            predictShortColor = 'green'
        else:
            predictShortText = f"{predictionResults[0][0]: .2f} USD ({predictionResults[0][1]: .2f}%)"
            predictShortColor = 'red'

        shortRelText = ""
        for i in range(len(predictionResults[0][2])):
            st = predictionResults[0][2][i]
            shortRelText += f"{st.companyName}, "
            if i % company_cnt == company_cnt - 1:
                shortRelText += '\n'
        if len(shortRelText) == 0:
            shortRelText = "(None)"
        elif shortRelText[-1] == '\n':
            shortRelText = shortRelText[:-3]
        else:
            shortRelText = shortRelText[:-2]

        trendShort.config(text=f"{trendShortText}", fg=trendShortColor)
        changeImpShort.config(text=f"{curStock.changeImportance[0]}", fg=changeImpShortColor)
        predictShort.config(text=predictShortText, fg=predictShortColor)
        relatedShort.config(text=shortRelText)

        # update long info
        trendLongPercent = curStock.stockChangeDataLong[-1] / curStock.stockDataLong[-2] * 100
        if curStock.stockChangeDataLong[-1] >= 0:
            trendLongColor = 'green'
            trendLongText = f'+{curStock.stockChangeDataLong[-1]: .2f} USD (+{trendLongPercent: .2f}%)'
        else:
            trendLongColor = 'red'
            trendLongText = f'{curStock.stockChangeDataLong[-1]: .2f} USD ({trendLongPercent: .2f}%)'

        if curStock.changeImportance[1]:
            changeImpLongColor = 'green'
        else:
            changeImpLongColor = 'red'

        if predictionResults[1][0] >= 0:
            predictLongText = f"+{predictionResults[1][0]: .2f} USD (+{predictionResults[1][1]: .2f}%)"
            predictLongColor = 'green'
        else:
            predictLongText = f"{predictionResults[1][0]: .2f} USD ({predictionResults[1][1]: .2f}%)"
            predictLongColor = 'red'

        longRelText = ""
        for i in range(len(predictionResults[1][2])):
            st = predictionResults[1][2][i]
            longRelText += f"{st.companyName}, "
            if i % company_cnt == company_cnt - 1:
                longRelText += '\n'
        if len(longRelText) == 0:
            longRelText = "(None)"
        elif longRelText[-1] == '\n':
            longRelText = longRelText[:-3]
        else:
            longRelText = longRelText[:-2]

        trendLong.config(text=f"{trendLongText}", fg=trendLongColor)
        changeImpLong.config(text=f"{curStock.changeImportance[1]}", fg=changeImpLongColor)
        predictLong.config(text=predictLongText, fg=predictLongColor)
        relatedLong.config(text=longRelText)

    def __findCanvasPos(
            self, canvas: Canvas, x_pad: int, y_pad: int, point_cnt: int, min_val: float, max_val: float,
            cnt: int, value: float) -> list:
        """
        Helper method for self.__updateSubFrame3() method.
        Finds correct canvas coordinate position based on given values (x_cnt & stock value).

        :param canvas: given Canvas Tkinter widget
        :param x_pad: padding in x-direction
        :param y_pad: padding in y-direction
        :param point_cnt: total number of points in x-direction
        :param min_val: minimum y-value
        :param max_val: maximum y-value
        :param cnt: current count in x-direction
        :param value: y-value
        :return: canvas coordinate list
        """
        # pad = axis_pad + point_pad

        raw_x = (cnt / (point_cnt - 1)) * (canvas.winfo_width() - x_pad)
        raw_y = (max_val - value) / (max_val - min_val) * (canvas.winfo_height() - 2 * y_pad) + y_pad
        return [raw_x, raw_y]

    def __findCanvasYPos(self, canvas: Canvas, y_pad: int, min_val: float, max_val: float, value: float) -> float:
        """
        Helper method for self.__updateSubFrame3() method.
        Finds correct y-coordinate canvas position based on given values (stock value).

        :param canvas: given Canvas Tkinter widget
        :param y_pad: padding in y-direction
        :param min_val: minimum y-value
        :param max_val: maximum y-value
        :param value: y-value
        :return: y-coordinate value
        """
        return (max_val - value) / (max_val - min_val) * (canvas.winfo_height() - 2 * y_pad) + y_pad

    def __calculatePrediction(self, curStock: Stock) -> list:
        """
        Helper method for self.__updateSubFrame3() method.
        Calculates predictions for given stock based on current stock data & company relations.

        :param curStock: currently selected Stock object
        :return:
            [(short prediction USD, short prediction %, short related stocks list),
            (long prediction USD, long prediction %, long related stocks list)]
        """
        curPrice = curStock.stockDataShort[-1]

        # short term
        shortRelStocks = dict()
        shortChange = curStock.stockChangeDataShort[-1]
        shortInfluence = 0
        shortRelDisplay = list()

        for stock in self.allStockList:
            if stock != curStock and stock.changeImportance[0]:
                query = f"{curStock.companyName}, {stock.companyName}"
                self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")
                shortRelStocks[stock] = (float(self.cur.fetchone()[0]) - minRelScore) / (maxRelScore - minRelScore)

        for stock in shortRelStocks.keys():
            shortInfluence += stock.stockChangeDataShort[-1] * shortRelStocks[stock]

        shortRelStocks = dict(sorted(shortRelStocks.items(), key=lambda x: x[1], reverse=True))

        for key in shortRelStocks:
            if shortRelStocks[key] >= 0.5:
                shortRelDisplay.append(key)

        # long term
        longRelStocks = dict()
        longChange = curStock.stockChangeDataLong[-1]
        longInfluence = 0
        longRelDisplay = list()

        for stock in self.allStockList:
            if stock != curStock and stock.changeImportance[1]:
                query = f"{curStock.companyName}, {stock.companyName}"
                self.cur.execute(f"select Final_Value from Relations where Companies = \'{query}\';")
                longRelStocks[stock] = (float(self.cur.fetchone()[0]) - minRelScore) / (maxRelScore - minRelScore)

        for stock in longRelStocks.keys():
            longInfluence += stock.stockChangeDataLong[-1] * longRelStocks[stock]

        longRelStocks = dict(sorted(longRelStocks.items(), key=lambda x: x[1], reverse=True))

        for key in longRelStocks:
            if longRelStocks[key] >= 0.5:
                longRelDisplay.append(key)

        return [
            (shortChange + shortInfluence, (shortChange + shortInfluence) / curPrice * 100, shortRelDisplay),
            (longChange + longInfluence, (longChange + longInfluence) / curPrice * 100, longRelDisplay)
        ]
