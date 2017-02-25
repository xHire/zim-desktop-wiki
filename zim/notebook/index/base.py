# -*- coding: utf-8 -*-

# Copyright 2009-2017 Jaap Karssenberg <jaap.karssenberg@gmail.com>


import logging

logger = logging.getLogger('zim.notebook.index')

from zim.signals import SignalEmitter, ConnectorMixin


class IndexNotFoundError(ValueError):
	'''Error used when lookup fails because a pagename does not appear
	in the index.
	'''
	pass


class IndexConsistencyError(AssertionError):
	'''Error used when a lookup fails while expected to succeed'''
	pass


class IndexView(object):
	'''Base class for "index view" objects'''

	@classmethod
	def new_from_index(cls, index):
		return cls(index._db)

	def __init__(self, db):
		self.db = db


class IndexerBase(SignalEmitter, ConnectorMixin):
	'''Base class for "content indexer" objects.
	It defines the callback functions that are calls from L{PagesIndexer}
	'''

	__signals__ = {}

	def __init__(self, db):
		self.db = db



class PluginIndexerBase(IndexerBase):
	'''Base class for indexers defined in plugins. These need some
	additional logic to allow them to be added and removed flexibly.
	See L{Index.add_plugin_indexer()} and L{Index.remove_plugin_indexer()}.

	Additional behavior required for plugin indexers:

	  - PLUGIN_NAME and PLUGIN_DB_FORMAT must be defined
	  - on_db_init() must be robust against data from
	    an older verion of the plugin being present. E.g. by first dropping
	    the plugin table and then initializing it again.
	  - on_db_teardown() needs to be implemented

	'''

	PLUGIN_NAME = None #: plugin name as string
	PLUGIN_DB_FORMAT = None #: version of the db scheme for this plugin as string

	def on_db_teardown(self):
		'''Callback that is called when the plugin is removed. Will not be
		called when the application exits.
		@implementation: must be overloaded by subclass
		'''
		raise NotImplementedError


class MyTreeIter(object):

	__slots__ = ('treepath', 'row', 'hint')

	def __init__(self, treepath, row, hint=None):
		self.treepath = treepath
		self.row = row
		self.hint = hint


class TreeModelMixinBase(ConnectorMixin):
    '''This class can be used as mixin class for C{gtk.TreeModel}
    implementations that use data from the index.

	Treepaths are simply tuples with integers. This Mixin assumes L{MyTreeIter}
	objects for iters. (Which should not be confused with C{gtk.TreeIter} as
	used by the interface!)
	'''

    def __init__(self, index):
        self.index = index
        self.db = index._db
        self.cache = {}
        self.connect_to_updateiter(index.update_iter)

	def connect_to_updateiter(self, update_iter):
		'''Connect to a new L{IndexUpdateIter}

		The following signals must be implemented:

		  - row-inserted (treepath, treeiter)
		  - row-changed (treepath, treeiter)
		  - row-has-child-toggled (treepath, treeiter)
		  - row-deleted (treepath)

		Typically each signal should also flush the cache using
		C{self.cache.clear()}.

	    @implementation: must be implemented by subclass
		'''
		raise NotImplementedError

    def teardown(self):
        self.flush_cache()
        self.disconnect_all()

	def n_children_top(self):
		'''Return the number of items in the top level of the model'''
		raise NotImplementedError

    def get_mytreeiter(self, treepath):
        '''Returens a C{treeiter} object for C{treepath} or C{None}
        @implementation: must be implemented by subclass
        '''
        raise NotImplementedError

	def find(self, obj):
		'''Return the treepath for a index object like a L{Path} or L{IndexTag}
		@raises IndexNotFoundError: if C{indexpath} is not found
		@implementation: must be implemented by subclass
		'''
		raise NotImplementedError

	def find_all(self, obj):
		'''Like L{find()} but can return multiple results
		@implementation: must be implemented by subclasses that have mutiple
		entries for the same object
		'''
		return [self.find(obj)]
