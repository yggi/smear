#SMEAR - SAX motif extraction and recognition#

written by Sebastian Steuer (steuers@cip.ifi.lmu.de)


##Requirements##

SMEAR depends on traits, traits.ui, and chaco.

traits is a type-system for python, traits.ui a MVC-framework and chaco is a chart plotting library. All three are made by [enthought](http://code.enthought.com)

* on debianesqes (ubuntu e.g.), try `sudo apt-get install python-chaco`. Go the hard way otherwise. (http://code.enthought.com/projects/chaco/docs/html/user_manual/installation.html)

##How to use##

* smear.py has help built-in. Try `python src/smear.py -h`

* plotter.py runs by itself and can:
  * load .arff/.wav/.sax data
  * select a slice of the sequence, select the parameters for the SAX-string generation
  * export the SAX-string as a .sax file for later comparison

* execute `python src/smear.py -c SAXFILE` to run a comparison of SAXFILE against all testdata and get a little evaluation (Precision, Recall, F1)
  * e.g `python src/smear.py -c sax/e_1_word4.sax`

you can also use the SAX-generator from an interactive python shell:

    cd src
    python
    >>> import sax
    >>> sax.saxify(range(100), epsilon = 20, word_size = 5, alphabet_size = 3)
    'AABCC'

##Data##

The /td folder contains .arff-files for ten different exercises (1-10) performed by 5 different persons (a-e). Each file contains 10 iterations of the exercise.

##What does not work##

* non-unix-systems: hardcoded paths at a few places, Windows won't work.
* data with more or less than six dimensions, or in general all data that isn't exactly written in the format that SMEAR excepts.
* No unittests yet, tbd
