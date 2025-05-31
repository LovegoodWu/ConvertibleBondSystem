import itertools
import os
from os.path import exists

import joblib
import backtrader as bt

smas = {}


class MyCerebro(bt.Cerebro):
    def __int__(self):
        super.__init__()

    def addstrategy(self, strategy, *args, **kwargs):
        '''
        添加策略，为保证可重复执行，需要清除之前添加过的策略
        如果你添加了多个策略，该方法需要增加判定清除条件。
        '''
        # if len(self.strats) == XX:
        #     self.strats.clear()
        self.strats.clear()
        self.strats.append([(strategy, args, kwargs)])
        return len(self.strats) - 1

    def optstrategy(self, strategy, *args, **kwargs):
        '''
        寻找最佳参数，为保证可重复执行，需要清除之前添加过的策略组合
        '''

        self.strats.clear()
        self._dooptimize = True
        args = self.iterize(args)
        optargs = itertools.product(*args)

        optkeys = list(kwargs)

        vals = self.iterize(kwargs.values())
        optvals = itertools.product(*vals)

        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)

        optkwargs = map(dict, okwargs1)

        it = itertools.product([strategy], optargs, optkwargs)
        self.strats.append(it)

    def _preloaddata(self):
        self._exactbars = int(self.p.exactbars)
        self._dopreload = self.p.preload
        for data in self.datas:
            data.reset()
            if self._exactbars < 1:  # datas can be full length
                data.extend(size=self.params.lookahead)
            data._start()
            if self._dopreload:
                data.preload()

    # 默认preload
    def dopreloaddata(self, cachedata=True, replacecache=False, cachefile='backtrader_tmp.joblib'):
        """
        cachedata: 是否缓存数据
        replacecache: 是否替换缓存
        cachefile: 缓存文件路径
        """
        # 处理缓存文件
        fileexist = exists(cachefile)
        # 如果缓存存在且需要重新加载则删除文件
        if replacecache and fileexist:
            os.remove(cachefile)
            # 文件状态更新
            fileexist = exists(cachefile)
        # 缓存文件不存在则加载数据
        if not fileexist:
            self._preloaddata()
            # 缓存到文件
            if cachedata:
                joblib.dump(self, cachefile)
        else:
            if cachedata:
                load = joblib.load(cachefile)
                self.analyzers = load.analyzers
                self.datas = load.datas
                self.broker = load.broker
                self.params = load.params
                self.p = load.p
                self.datasbyname = load.datasbyname
            else:
                self._preloaddata()

    def run(self, **kwargs):
        self._event_stop = False  # Stop is requested

        if not self.datas:
            return []  # nothing can be run

        pkeys = self.params._getkeys()
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)

        # Manage activate/deactivate object cache
        bt.linebuffer.LineActions.cleancache()  # clean cache
        bt.indicator.Indicator.cleancache()  # clean cache

        bt.linebuffer.LineActions.usecache(self.p.objcache)
        bt.indicator.Indicator.usecache(self.p.objcache)

        self._dorunonce = self.p.runonce
        self._dopreload = self.p.preload
        self._exactbars = int(self.p.exactbars)

        if self._exactbars:
            self._dorunonce = False  # something is saving memory, no runonce
            self._dopreload = self._dopreload and self._exactbars < 1

        self._doreplay = self._doreplay or any(x.replaying for x in self.datas)
        if self._doreplay:
            # preloading is not supported with replay. full timeframe bars
            # are constructed in realtime
            self._dopreload = False

        if self._dolive or self.p.live:
            # in this case both preload and runonce must be off
            self._dorunonce = False
            self._dopreload = False

        self.runwriters = list()

        # Add the system default writer if requested
        if self.p.writer is True:
            wr = bt.WriterFile()
            self.runwriters.append(wr)

        # Instantiate any other writers
        for wrcls, wrargs, wrkwargs in self.writers:
            wr = wrcls(*wrargs, **wrkwargs)
            self.runwriters.append(wr)

        # Write down if any writer wants the full csv output
        self.writers_csv = any(map(lambda x: x.p.csv, self.runwriters))

        self.runstrats = list()

        if self.signals:  # allow processing of signals
            signalst, sargs, skwargs = self._signal_strat
            if signalst is None:
                # Try to see if the 1st regular strategy is a signal strategy
                try:
                    signalst, sargs, skwargs = self.strats.pop(0)
                except IndexError:
                    pass  # Nothing there
                else:
                    if not isinstance(signalst, bt.SignalStrategy):
                        # no signal ... reinsert at the beginning
                        self.strats.insert(0, (signalst, sargs, skwargs))
                        signalst = None  # flag as not presetn

            if signalst is None:  # recheck
                # Still None, create a default one
                signalst, sargs, skwargs = bt.SignalStrategy, tuple(), dict()

            # Add the signal strategy
            self.addstrategy(signalst,
                             _accumulate=self._signal_accumulate,
                             _concurrent=self._signal_concurrent,
                             signals=self.signals,
                             *sargs,
                             **skwargs)

        if not self.strats:  # Datas are present, add a strategy
            self.addstrategy(bt.Strategy)

        iterstrats = bt.itertools.product(*self.strats)
        if not self._dooptimize or self.p.maxcpus == 1:
            # If no optimmization is wished ... or 1 core is to be used
            # let's skip process "spawning"
            for iterstrat in iterstrats:
                runstrat = self.runstrategies(iterstrat)
                self.runstrats.append(runstrat)
                if self._dooptimize:
                    for cb in self.optcbs:
                        cb(runstrat)  # callback receives finished strategy
        else:
            # 移动到dopreload
            # if self.p.optdatas and self._dopreload and self._dorunonce:
            #     for data in self.datas:
            #         data.reset()
            #         if self._exactbars < 1:  # datas can be full length
            #             data.extend(size=self.params.lookahead)
            #         data._start()
            #         if self._dopreload:
            #             data.preload()

            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.reset()
                    data._start()
            pool = bt.multiprocessing.Pool(self.p.maxcpus or None)
            for r in pool.imap(self, iterstrats):
                self.runstrats.append(r)
                for cb in self.optcbs:
                    cb(r)  # callback receives finished strategy

            pool.close()

            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.reset()
                    data._start()

        if not self._dooptimize:
            # avoid a list of list for regular cases
            return self.runstrats[0]

        return self.runstrats

    def runstrategies(self, iterstrat, predata=False):
        '''
        Internal method invoked by ``run```to run a set of strategies
        '''
        self._init_stcount()

        self.runningstrats = runstrats = list()
        for store in self.stores:
            store.start()

        if self.p.cheat_on_open and self.p.broker_coo:
            # try to activate in broker
            if hasattr(self._broker, 'set_coo'):
                self._broker.set_coo(True)

        if self._fhistory is not None:
            self._broker.set_fund_history(self._fhistory)

        for orders, onotify in self._ohistory:
            self._broker.add_order_history(orders, onotify)

        self._broker.start()

        for feed in self.feeds:
            feed.start()

        if self.writers_csv:
            wheaders = list()
            for data in self.datas:
                if data.csv:
                    wheaders.extend(data.getwriterheaders())

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addheaders(wheaders)

        # self._plotfillers = [list() for d in self.datas]
        # self._plotfillers2 = [list() for d in self.datas]

        for stratcls, sargs, skwargs in iterstrat:
            sargs = self.datas + list(sargs)
            try:
                strat = stratcls(*sargs, **skwargs)
            except bt.errors.StrategySkipError:
                continue  # do not add strategy to the mix

            if self.p.oldsync:
                strat._oldsync = True  # tell strategy to use old clock update
            if self.p.tradehistory:
                strat.set_tradehistory()
            runstrats.append(strat)

        tz = self.p.tz
        if isinstance(tz, bt.integer_types):
            tz = self.datas[tz]._tz
        else:
            tz = bt.tzparse(tz)

        if runstrats:
            # loop separated for clarity
            defaultsizer = self.sizers.get(None, (None, None, None))
            for idx, strat in enumerate(runstrats):
                if self.p.stdstats:
                    strat._addobserver(False, bt.observers.Broker)
                    if self.p.oldbuysell:
                        strat._addobserver(True, bt.observers.BuySell)
                    else:
                        strat._addobserver(True, bt.observers.BuySell,
                                           barplot=True)

                    if self.p.oldtrades or len(self.datas) == 1:
                        strat._addobserver(False, bt.observers.Trades)
                    else:
                        strat._addobserver(False, bt.observers.DataTrades)

                for multi, obscls, obsargs, obskwargs in self.observers:
                    strat._addobserver(multi, obscls, *obsargs, **obskwargs)

                for indcls, indargs, indkwargs in self.indicators:
                    strat._addindicator(indcls, *indargs, **indkwargs)

                for ancls, anargs, ankwargs in self.analyzers:
                    strat._addanalyzer(ancls, *anargs, **ankwargs)

                sizer, sargs, skwargs = self.sizers.get(idx, defaultsizer)
                if sizer is not None:
                    strat._addsizer(sizer, *sargs, **skwargs)

                strat._settz(tz)
                strat._start()

                for writer in self.runwriters:
                    if writer.p.csv:
                        writer.addheaders(strat.getwriterheaders())

            if not predata:
                for strat in runstrats:
                    strat.qbuffer(self._exactbars, replaying=self._doreplay)

            for writer in self.runwriters:
                writer.start()

            # Prepare timers
            self._timers = []
            self._timerscheat = []
            for timer in self._pretimers:
                # preprocess tzdata if needed
                timer.start(self.datas[0])

                if timer.params.cheat:
                    self._timerscheat.append(timer)
                else:
                    self._timers.append(timer)

            if self._dopreload and self._dorunonce:
                if self.p.oldsync:
                    self._runonce_old(runstrats)
                else:
                    self._runonce(runstrats)
            else:
                if self.p.oldsync:
                    self._runnext_old(runstrats)
                else:
                    self._runnext(runstrats)

            for strat in runstrats:
                strat._stop()

        self._broker.stop()

        if not predata:
            for data in self.datas:
                data.stop()

        for feed in self.feeds:
            feed.stop()

        for store in self.stores:
            store.stop()

        self.stop_writers(runstrats)

        if self._dooptimize and self.p.optreturn:
            # Results can be optimized
            results = list()
            for strat in runstrats:
                for a in strat.analyzers:
                    a.strategy = None
                    a._parent = None
                    for attrname in dir(a):
                        if attrname.startswith('data'):
                            setattr(a, attrname, None)

                oreturn = bt.OptReturn(strat.params, analyzers=strat.analyzers, strategycls=type(strat))
                results.append(oreturn)

            return results

        return runstrats
