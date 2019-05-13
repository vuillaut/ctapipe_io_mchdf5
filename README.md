[![Build Status](https://travis-ci.org/cta-observatory/ctapipe_io_mchdf5.svg?branch=master)](https://travis-ci.org/cta-observatory/ctapipe_io_mchdf5)

ctapipe plugin for reading Monte-Carlo files (contains the same informations as Simtel files)

Installation
============

```sh
  $ git clone https://github.com/cta-observatory/ctapipe_io_mchdf5.git
  $ cd ctapipe_io_mchdf5
  $ python setup.py install
```

Simtel file conversion
======================

```sh
  $ simtel2hdf5 -i inputFile.simtel.gz -o outputFile.h5
```
