.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/stateful-data-processor.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/stateful-data-processor
    .. image:: https://readthedocs.org/projects/stateful-data-processor/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://stateful-data-processor.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/stateful-data-processor/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/stateful-data-processor
    .. image:: https://img.shields.io/pypi/v/stateful-data-processor.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/stateful-data-processor/
    .. image:: https://img.shields.io/conda/vn/conda-forge/stateful-data-processor.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/stateful-data-processor
    .. image:: https://pepy.tech/badge/stateful-data-processor/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/stateful-data-processor
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/stateful-data-processor

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

=======================
stateful-data-processor
=======================


    Utility to process data incrementally and save the state to a file.


Problem: let's say you have a large amount of data, that you want to loop through and process incrementally.
Processing takes time, and in case an error occurs, you do not want to lose all the progress.
You want to save the data to a file and be able to continue processing from where you left off.
You also want to be able to interrupt the processing with a SIGINT signal and save the data to the file.
You want to be able to subclass the processor and implement the process_data and process_item methods.
You want to be able to iterate through items and process them one by one.

StatefulDataProcessor class to process data incrementally.
    Process large amounts of data in a JSON file incrementally.

    The data is stored in a dictionary and the processor keeps track of the current step being processed.

    The processor can be interrupted with a SIGINT signal and the data will be saved to the file.
    
    The processor is meant to be subclassed and the process_data method should be implemented.
    
    The process_item method should be implemented to process a single item, if iterate_items is used.


.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.
