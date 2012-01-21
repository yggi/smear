import os
from numpy import linspace, sin

from enthought.traits.api import HasTraits, Instance, Array, Property, on_trait_change, Enum, List, Int, Bool, Range, Str,Button
from enthought.traits.ui.api import View, Item, Group
from enthought.pyface.api import FileDialog, OK, confirm, YES

from enthought.chaco.api import ArrayDataSource,VPlotContainer,HPlotContainer, OverlayPlotContainer, Plot, ArrayPlotData,DataLabel
from enthought.chaco.tools.api import RangeSelection, RangeSelectionOverlay

from enthought.enable.api import ComponentEditor, Component

import smear
#from smear import RawData

class SmearPlot(HasTraits):
    plot_colors = List(["red", "green", "blue", "cyan", "magenta", "orange"])
    plot_names = List(["accX", "accY", "accZ", "gyrX", "gyrY", "gyrZ"])

    filedir = Str
    filename = Str
    load_button = Button('Load')
    save_as_button = Button('Save Motif')
    file_wildcard = Str("All files|*")
    sax_wildcard = Str("SAX file (*.sax)|*.sax")

    plot = Instance(Component)
    raw = Instance(smear.RawData)
    selector = Instance(RangeSelection)
    x1 = Int
    x2 = Int
    normalize = Bool
    epsilon = Range(low=0, high=200, value=50)
    paa = Bool
    word_size = Range(low=1, high=20, value=6)
    sax = Bool
    alphabet_size = Range(low=3, high=7, value=5)
    aps = Instance(list)
    selected_length = Property(Int, depends_on=["x1","x2"])
    data_selected = Instance(smear.RawData)

    id1 = Str
    id2 = Str
    id3 = Str

    w1 = Range(low=0.0,high=1.0,value=0.5)
    w2 = Range(low=0.0,high=1.0,value=0.5)
    w3 = Range(low=0.0,high=1.0,value=0.5)
    w4 = Range(low=0.0,high=1.0,value=0.5)
    w5 = Range(low=0.0,high=1.0,value=0.5)
    w6 = Range(low=0.0,high=1.0,value=0.5)

    window_min = Int
    window_max = Int
    window_step = Int

    dist_max = Range(low=0.0, high=1.0, value = 0.1)
    #test_selected = Property(List, depends_on=["x1","x2"])

    traits_view = View(
        Group(
        Group(Item('plot',editor=ComponentEditor(), show_label=False),
                   Group(Item('w1'),Item('w2'),Item('w3'),Item('w4'),Item('w5'),Item('w6'), orientation="vertical"), orientation="horizontal"),
        Group(Group(Item('x1'), Item('x2'), Item ('selected_length'), orientation="horizontal"),
            Group(Item('normalize'), Item('epsilon'), orientation="horizontal"),
            Group(Item("paa"), Item("word_size"), orientation="horizontal"),
            Group(Item("sax"), Item("alphabet_size"), orientation="horizontal"),
            Group(Item("id1"),Item("id2"),Item("id3"), orientation="horizontal"),
            Group(Item("window_min"), Item("window_max"), Item("window_step"), Item("dist_max"), orientation="horizontal"),
            Group(Item('load_button'), Item('save_as_button'), orientation="horizontal"),
            orientation = "vertical", layout="normal"), layout="normal"),
    width=500, height=500, resizable=True, title="SMEAR - SAX motif extraction and recognition",dock="fixed")
    def __init__(self,data):
        super(SmearPlot, self).__init__()
        self.init(data)

    def init(self,data):
        self.raw = data
        self.data_selected = data
        index = range(self.raw.length)
        self.x1 = 0
        self.x2 = self.raw.length

        self.epsilon = self.data_selected.epsilon
        self.word_size = self.data_selected.word_size
        self.alphabet_size = self.data_selected.alphabet_size

        self.id1 = self.data_selected.id1
        self.id2 = self.data_selected.id2
        self.id3 = self.data_selected.id3

        self.window_min = self.data_selected.window_min
        self.window_max = self.data_selected.window_max
        self.window_step = self.data_selected.window_step

        self.dist_max = self.data_selected.dist_max

        overviewkwargs = {}
        for (dim,i) in zip(self.raw.data_transposed, range(len(self.plot_names))):
            overviewkwargs[self.plot_names[i]] = dim

        overviewdata = ArrayPlotData(index=index, **overviewkwargs)
        overview = Plot(overviewdata)

        axiscontainer = VPlotContainer()
        axiscontainer.spacing = 0
        aps = []
        paastep = self.selected_length / (len(self.data_selected.data_paaed[0]))
        paaindex = range(paastep/2,self.selected_length, paastep)

        for (dim,i) in zip(self.raw.data_transposed, range(len(self.plot_names))):
            overview.plot(("index",self.plot_names[i]),
                          type="line",
                          color=self.plot_colors[i])

            ap = Plot(ArrayPlotData(index = index,
                                    paaindex = paaindex,
                                    paa = self.data_selected.data_paaed[i],
                                    **{self.plot_names[i]:self.data_selected.data_transposed[i]}))

            ap.plot(("index",self.plot_names[i]), type="line", color=self.plot_colors[i])
            ap.plot(("paaindex","paa"), type="scatter", color=self.plot_colors[i])
            #ap.title = a["name"]
            ap.padding_top = 1
            ap.padding_bottom = 0
            ap.y_axis.orientation = "right"
            axiscontainer.add(ap)
            aps.append(ap)
            ap.components[1].visible = False

        self.aps = aps

        rs = RangeSelection(overview.components[0], left_button_selects= True)
        self.selector = rs
        overview.components[0].tools.append(rs)
        overview.components[0].overlays.append(RangeSelectionOverlay(component=overview.components[0]))

        lrcontainer = HPlotContainer(overview,axiscontainer)

        lrcontainer.spacing = 0
        self.plot = lrcontainer

    def update(self):
        if self.normalize:
            d = self.data_selected.data_normalized
        else:
            d = self.data_selected.data_transposed


        if self.selected_length % (len(self.data_selected.data_paaed[0]))==0:
            paastep = self.selected_length / (len(self.data_selected.data_paaed[0]))
        else:
            paastep = self.selected_length / (len(self.data_selected.data_paaed[0]))+1

        if paastep >= 1:
            paaindex = [x+paastep/2 for x in range(0,self.selected_length, paastep)]

        for i in range(6):
            #ap = Plot(ArrayPlotData(index = range(self.selected_length), **{self.plot_names[i]:self.data_selected[i]}))
            #ap.plot(("index",self.plot_names[i]), type="line", color=self.plot_colors[i])

            self.aps[i].components[0].value = ArrayDataSource(d[i])
            self.aps[i].components[0].index = ArrayDataSource(range(self.selected_length))
            mx = self.aps[i].components[0].index_mapper.range
            mx.low = 0
            mx.high = self.selected_length

            my = self.aps[i].components[0].y_mapper.range#
            my.low = min(d[i])
            my.high = max(d[i])
            #self.aps[i].components[0].visible = True
            if self.paa:
                self.aps[i].components[1].visible = True
            else:
                self.aps[i].components[1].visible = False

            if paastep>=1 and self.paa:
                #print len(paaindex), len(self.data_selected.data_paaed[i])
                self.aps[i].components[1].value = ArrayDataSource(self.data_selected.data_paaed[i])
                self.aps[i].components[1].index = ArrayDataSource(paaindex)
            else:
                self.aps[i].components[1].value = None

            try:
                self.aps[i].components[1].overlays = []
                if self.sax:
                    for x in range(len(self.data_selected.data_saxed[0])):
                        sax_char = self.data_selected.data_saxed[i][x]
                        label = DataLabel(self.aps[i].components[1], data_point=(paaindex[x],self.data_selected.data_paaed[i][x]), lines=[sax_char])
                        self.aps[i].components[1].overlays.append(label)
                        #print i, x, sax_char, len(self.data_selected.data_paaed[i])
            except (IndexError):
                pass

    @on_trait_change('selector.selection')
    def _calculate_area(self):
        if self.selector.selection is not None and len(self.selector.selection) == 2:
            self.x1 = int(min(self.selector.selection))
            self.x2 = int(max(self.selector.selection))
            self.data_selected = self.raw[self.x1:self.x2]
            self.window_min = self.selected_length
            self.window_max = self.selected_length
            self.data_selected.id1 = self.raw.id1
            self.data_selected.id2 = self.raw.id2
            self.data_selected.id3 = self.raw.id3
        self.update

    def _get_selected_length(self):
        return self.x2-self.x1

    def _x1_changed(self):
        self.update()

    def _x2_changed(self):
        self.update()

    def _normalize_changed(self):
        self.update()

    def _paa_changed(self):
        self.update()

    def _word_size_changed(self):
        self.data_selected.word_size = self.word_size
        self.update()

    def _epsilon_changed(self):
        self.data_selected.epsilon = self.epsilon
        self.update()

    def _sax_changed(self):
        self.update()
        self.update()

    def _alphabet_size_changed(self):
        self.data_selected.alphabet_size = self.alphabet_size

    def _id1_changed(self):
        self.data_selected.id1 = self.id1

    def _id2_changed(self):
        self.data_selected.id2 = self.id2

    def _id3_changed(self):
        self.data_selected.id3 = self.id3

    def _window_min_changed(self):
        self.data_selected.window_min = self.window_min

    def _window_max_changed(self):
        self.data_selected.window_max = self.window_max

    def _window_step_changed(self):
        self.data_selected.window_step = self.window_step

    def _dist_max_changed(self):
        print "dist changed"
        self.data_selected.dist_max = self.dist_max

    def _load_button_fired(self):
        dialog = FileDialog(action = "open", wildcard=self.file_wildcard)
        dialog.open()
        if dialog.return_code == OK:
            self.init(smear.RawData(dialog.path))
            #self.raw = smear.RawData(dialog.path, 'r')
            self.filename = dialog.filename

    def _save_as_button_fired(self):
        dialog = FileDialog(action="save as", wildcard=self.sax_wildcard)
        dialog.open()
        if dialog.return_code == OK:
            self.data_selected.save_sax(dialog.path)

if __name__ == "__main__":
    d = smear.RawData("../td/exercise-1a.arff")
    SmearPlot(d).configure_traits()
