import pandas as pd
from pyecharts.charts import Kline, Bar
from pyecharts import options as opts
import os
import webbrowser
from datetime import datetime, timedelta

'''
缠中说禅分析
'''

class ChanLun:

    def __init__(self, klines):
        self.klines_orig_df = klines # 原始K线, dataframe格式
        self.klines_orig = klines_h.to_dict(orient='records')  # 原始K线, list格式
        self.klines_merge = []  # 合并后的K线
        self.fxs = []  # 分型
        self.pens = []  # 笔列表
        self.hubs = []  # 中枢列表
        self.status = "未确定"
        self.is_in_hub = False  # 当前是否在中枢内
        self.merge()
        self.check_merge()
        self.kline_fx()
        self.kline_pen()
        self.kline_hub()
        self.update_status()
        # self.draw()

    '''
    数据绘制分段
    '''

    def split_data_for_kline(self):
        mark_line_data = []
        idx = 0
        for i in range(len(self.klines_merge)):
            for pen in self.pens:
                if pen['fx']["k2"]['datetime'] == self.klines_merge[i]['datetime']:
                    mark_line_data.append(
                        [
                            {
                                "xAxis": idx,
                                "yAxis": self.klines_merge[idx]['high'] if pen["mark"] == 'up' else self.klines_merge[idx]['low'],
                            },
                            {
                                "xAxis": i,
                                "yAxis": pen['price'],
                            }
                        ]
                    )
                    idx = i
                    break
        return mark_line_data

    def split_data_for_hub(self):
        mark_line_data = []
        for hub in self.hubs:
            mark_line_data.append(
                [
                    {
                        "xAxis": hub['start_datetime'],
                        "yAxis": hub['high_price'],
                    },
                    {
                        "xAxis": hub['end_datetime'],
                        "yAxis": hub['low_price'],
                    }
                ]
            )

        return mark_line_data

    '''
    绘制
    '''

    def draw(self, freq=""):
        kdata = []
        ktime = []
        kvol = []
        for i in range(len(self.klines_merge)):
            current_kline = self.klines_merge[i]
            onedata = []  # [开盘值, 收盘值,最低值, 最高值]
            onedata.append(current_kline['high'])
            onedata.append(current_kline['low'])
            onedata.append(current_kline['low'])
            onedata.append(current_kline['high'])
            kdata.append(onedata)
            ktime.append(current_kline['datetime'])
            kvol.append(current_kline['volume'])
        kline = (
            Kline().add_xaxis(ktime).add_yaxis(series_name=self.klines_merge[0]['code'], y_axis=kdata,
                                               markline_opts=opts.MarkLineOpts(label_opts=opts.LabelOpts(position="middle", color="blue", font_size=15),
                                                                               data=self.split_data_for_kline(),
                                                                               symbol=["circle", "none"], ),
                                               )
            .set_global_opts(xaxis_opts=opts.AxisOpts(is_scale=True),
                             yaxis_opts=opts.AxisOpts(is_scale=True,
                                                      splitarea_opts=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)),
                                                      ),
                             datazoom_opts=[opts.DataZoomOpts()],
                             title_opts=opts.TitleOpts(title=self.klines_merge[0]['code']),
                             )
            .set_series_opts(
                markarea_opts=opts.MarkAreaOpts(is_silent=True, data=self.split_data_for_hub())
            )
        )

        bar = (Bar().add_xaxis(ktime).add_yaxis("", kvol))
        path = f"{os.path.expanduser('~/Downloads/')}/" + self.klines_merge[0]['code'] + "-" + freq + ".html"
        kline.render(path)
        webbrowser.open('file://' + path)

    '''
    检查函数
    '''

    def check_merge(self):
        for i in range(len(self.klines_merge) - 1, -1, -1):
            if i < 1:
                return
            current_kline = self.klines_merge[i]
            second_kline = self.klines_merge[i - 1]
            if (current_kline['low'] <= second_kline['low'] and current_kline['high'] >= second_kline['high']) or \
                    (current_kline['low'] >= second_kline['low'] and current_kline['high'] <= second_kline['high']):
                print("wrong merge")
                print(current_kline)
                print(second_kline)

    def has_kine(self, begin, end):
        b_start = False
        for i in range(self.klines_merge):
            current_kline = self.klines_merge[i]
            if current_kline['datetime'] == begin:
                b_start = True
                continue
            if b_start and current_kline['datetime'] < end:
                return True
        return False

    '''
    更新状态为上涨、分型、下跌
    '''

    def update_status(self):
        if len(self.pens) > 0:
            if self.pens[-1]['fx']['k3']['datetime'] == self.klines_merge[-1]['datetime']:
                if self.pens[-1]['fx']['mark'] == 'h':
                    self.status = "顶分型"
                else:
                    self.status = "底分型"
            else:
                if self.pens[-1]['fx']['mark'] == 'h':
                    self.status = "下降笔"
                else:
                    self.status = "上升笔"

    '''
    计算中枢
    '''

    def kline_hub(self, bold=False):
        pen_len = len(self.pens)
        if pen_len < 7:
            print("pen is less then 7，cant calculate hub")
            return
        i = 0
        up_layer = 0
        down_layer = 0
        while i <= pen_len - 7:
            if self.pens[0 + i]['mark'] == 'up':
                # 第0笔的起点价格低于第2笔的起点 且 第0笔的起点价格低于第4笔的起点
                if self.pens[0 + i]['price'] < self.pens[2 + i]['price'] and self.pens[0 + i]['price'] < self.pens[4 + i]['price'] and self.pens[1 + i]['price'] >= \
                        self.pens[4 + i]['price']:
                    hub = {}
                    hub['start_datetime'] = self.pens[1 + i]['fx']['k2']['datetime']
                    hub['low_price'] = max(self.pens[2 + i]['price'], self.pens[4 + i]['price'])
                    hub['high_price'] = min(self.pens[1 + i]['price'], self.pens[3 + i]['price'])
                    # if hub['high_price'] < hub['low_price']:
                    #     tmp = hub['high_price']
                    #     hub['high_price'] = hub['low_price']
                    #     hub['low_price'] = tmp

                    j = 0
                    while True:
                        # while j <= fblen - 6 - i - 1:
                        # 同方向跳出中枢
                        if self.pens[6 + i + j]['price'] > hub['high_price'] and self.pens[5 + i + j]['price'] > hub['high_price']:
                            hub['end_datetime'] = self.pens[4 + i + j]['fx']['k2']['datetime']
                            hub['signal_price'] = self.pens[6 + i + j]['price']
                            hub['signal_datetime'] = self.pens[6 + i + j]['fx']['k2']['datetime']
                            hub['mark'] = 'up'
                            if down_layer == 0:
                                up_layer = up_layer + 1
                                hub['layer'] = up_layer
                            else:
                                down_layer = 0
                                up_layer = 1
                                hub['layer'] = up_layer

                            self.hubs.append(hub)
                            i = 4 + i + j
                            break
                        # 反方向跳出中枢，无法构成中枢
                        if self.pens[5 + i + j]['price'] < hub['low_price'] and self.pens[6 + i + j]['price'] < hub['low_price']:
                            # hub['end_datetime'] = self.pens[4 + i + j]['fx']['k2']['datetime']
                            # hub['signal_price'] = self.pens[6 + i + j]['price']
                            # hub['signal_datetime'] = self.pens[6 + i + j]['fx']['k2']['datetime']
                            # hub['mark'] = 'up-down'
                            # self.hubs.append(hub)
                            # i = 4 + i + j
                            i = i + 1
                            break
                        else:
                            if 6 + i + j + 1 < pen_len:
                                j = j + 1
                                self.is_in_hub = True
                            else:
                                i = i + 1
                                # self.is_in_hub = False
                                break
                    # i = i + 1
                else:
                    i = i + 1
                    self.is_in_hub = False
            elif self.pens[0 + i]['mark'] == 'down':
                if self.pens[0 + i]['price'] > self.pens[2 + i]['price'] and self.pens[0 + i]['price'] > self.pens[4 + i]['price'] and self.pens[1 + i]['price'] <= \
                        self.pens[4 + i]['price']:
                    hub = {}
                    hub['start_datetime'] = self.pens[1 + i]['fx']['k2']['datetime']
                    hub['low_price'] = max(self.pens[1 + i]['price'], self.pens[3 + i]['price'])
                    hub['high_price'] = min(self.pens[2 + i]['price'], self.pens[4 + i]['price'])
                    # if hub['high_price'] < hub['low_price']:
                    #     tmp = hub['high_price']
                    #     hub['high_price'] = hub['low_price']
                    #     hub['low_price'] = tmp
                    j = 0
                    while True:
                        # while j <= fblen - 6 - i - 1:
                        # 同方向跳出才能构成中枢
                        if self.pens[6 + i + j]['price'] < hub['low_price'] and self.pens[5 + i + j]['price'] < hub['low_price']:
                            hub['end_datetime'] = self.pens[4 + i + j]['fx']['k2']['datetime']
                            hub['signal_price'] = self.pens[6 + i + j]['price']
                            hub['signal_datetime'] = self.pens[6 + i + j]['fx']['k2']['datetime']
                            hub['mark'] = 'down'
                            if up_layer == 0:
                                down_layer = down_layer + 1
                                hub['layer'] = down_layer
                            else:
                                up_layer = 0
                                down_layer = 1
                                hub['layer'] = down_layer
                            self.hubs.append(hub)
                            i = 4 + i + j
                            break
                        # 反方向跳出无法构成中枢
                        if self.pens[5 + i + j]['price'] > hub['high_price'] and self.pens[6 + i + j]['price'] > hub['high_price']:
                            # hub['end_datetime'] = self.pens[4 + i + j]['fx']['k2']['datetime']
                            # hub['signal_price'] = self.pens[6 + i + j]['price']
                            # hub['signal_datetime'] = self.pens[6 + i + j]['fx']['k2']['datetime']
                            # hub['mark'] = 'down-up'
                            # self.hubs.append(hub)
                            # i = 4 + i + j
                            i = i + 1
                            break
                        else:
                            if 6 + i + j + 1 < pen_len:
                                j = j + 1
                                self.is_in_hub = True
                            else:
                                i = i + 1
                                # self.is_in_hub = False
                                break
                else:
                    i = i + 1
                    self.is_in_hub = False

    '''
    笔划分，笔包括开始点分型、类型（up或down）、分型中间点最值价格
    {'fx': {'mark': 'h', 'low': 16.54, 'high': 18.1,
    'k1': {'datetime': '2020-10-16', 'code': 'sz.000001', 'open': 16.56, 'high': 17.37, 'low': 16.54, 'close': 17.1, 'volume': 209561419, 'amount': 3589229558.57, 'adjustflag': 2}, 
    'k2': {'datetime': '2020-10-19', 'code': 'sz.000001', 'open': 17.3, 'high': 18.1, 'low': 17.3, 'close': 17.48, 'volume': 201610552, 'amount': 3571336006.25, 'adjustflag': 2}, 
    'k3': {'datetime': '2020-10-20', 'code': 'sz.000001', 'open': 17.48, 'high': 17.6, 'low': 17.25, 'close': 17.54, 'volume': 96007195, 'amount': 1673173355.65, 'adjustflag': 2}, 
    'datetime': '2020-10-19'}, 
    'mark': 'up', 'price': 18.1}
    '''

    def kline_pen(self, bold=False):
        fxlen = len(self.fxs)
        if fxlen < 2:
            print("fx is less then 2")
        fx_count = len(self.fxs)
        for i in range(fx_count):
            current_fx = self.fxs[i]
            if len(self.pens) == 0:
                current_pen = {}
                current_pen['fx'] = current_fx
                current_pen['mark'] = 'down' if current_fx['mark'] == 'h' else 'up'
                current_pen['price'] = current_fx['k2']['low'] if current_fx['mark'] == 'l' else current_fx['k2']['high']
                self.pens.append(current_pen)
            else:
                last_bi = self.pens[-1]
                current_pen = {}
                if last_bi['mark'] == "up":
                    # 延续
                    if current_fx['mark'] == 'l':
                        if current_fx['k2']['low'] < last_bi['price']:
                            self.pens[-1]['fx'] = current_fx
                            self.pens[-1]['price'] = current_fx['k2']['low']
                    if current_fx['mark'] == 'h':
                        # 不共用K线
                        if current_fx["k1"]['datetime'] > last_bi['fx']['k3']['datetime']:
                            # 老笔必须有独立k
                            if bold == True and self.has_kine(last_bi['fx']['k3']['datetime'], current_fx["k1"]['datetime']):
                                current_pen = {}
                                current_pen['fx'] = current_fx
                                current_pen['mark'] = 'down'
                                current_pen['price'] = current_fx['k2']['high']
                                self.pens.append(current_pen)
                            else:
                                current_pen = {}
                                current_pen['fx'] = current_fx
                                current_pen['mark'] = 'down'
                                current_pen['price'] = current_fx['k2']['high']
                                self.pens.append(current_pen)
                if last_bi['mark'] == "down":
                    # 延续
                    if current_fx['mark'] == 'h':
                        if current_fx['k2']['high'] > last_bi['price']:
                            self.pens[-1]['fx'] = current_fx
                            self.pens[-1]['price'] = current_fx['k2']['high']
                    if current_fx['mark'] == 'l':
                        # 不共用K线
                        if current_fx["k1"]['datetime'] > last_bi['fx']['k3']['datetime']:
                            # 老笔必须有独立k
                            if bold == True and self.has_kine(last_bi['fx']['k3']['datetime'], current_fx["k1"]['datetime']):
                                current_pen = {}
                                current_pen['fx'] = current_fx
                                current_pen['mark'] = 'up'
                                current_pen['price'] = current_fx['k2']['low']
                                self.pens.append(current_pen)
                            else:
                                current_pen = {}
                                current_pen['fx'] = current_fx
                                current_pen['mark'] = 'up'
                                current_pen['price'] = current_fx['k2']['low']
                                self.pens.append(current_pen)

    '''
    分型
    {'fx': {'mark': 'l', 'low': 15.12, 'high': 15.27, 
    'k1': {'datetime': '2020-09-24', 'code': 'sz.000001', 'open': 15.59, 'high': 15.61, 'low': 15.12, 'close': 15.12, 'volume': 106101124, 'amount': 1623376200.81, 'adjustflag': 2}, 
    'k2': {'datetime': '2020-09-25', 'code': 'sz.000001', 'open': 15.2, 'high': 15.27, 'low': 14.76, 'close': 15.19, 'volume': 61408700, 'amount': 933035044.47, 'adjustflag': 2}, 
    'k3': {'datetime': '2020-10-09', 'code': 'sz.000001', 'open': 15.3, 'high': 15.55, 'low': 15.13, 'close': 15.18, 'volume': 90042593, 'amount': 1376995906.6, 'adjustflag': 2},
    'datetime': '2020-10-09'
    }
    '''

    def kline_fx(self):
        if len(self.klines_merge) < 3:
            print("kline_merge is less")
            return

        for i in range(len(self.klines_merge)):
            if i < 2:
                continue
            first_k = self.klines_merge[i - 2]
            second_k = self.klines_merge[i - 1]
            third_k = self.klines_merge[i]
            # 顶分型
            if (second_k['high'] > first_k['high'] and second_k['high'] > third_k['high']) and \
                    (second_k['low'] > first_k['low'] and second_k['low'] > third_k['low']):
                fx = {}
                fx['mark'] = 'h'
                fx['low'] = first_k['low']
                fx['high'] = second_k['high']
                fx['datetime'] = second_k['datetime']
                fx['k1'] = first_k
                fx['k2'] = second_k
                fx['k3'] = third_k

                kdj=self.get_kdj(second_k['datetime'])
                fx['K']=kdj['K'].iloc[-1]
                fx['D'] = kdj['D'].iloc[-1]
                fx['J'] = kdj['J'].iloc[-1]
                self.fxs.append(fx)
            # 底分型
            if (second_k['low'] < first_k['low'] and second_k['low'] < third_k['low']) and \
                    (second_k['high'] < first_k['high'] and second_k['high'] < third_k['high']):
                fx = {}
                fx['mark'] = 'l'
                fx['low'] = second_k['low']
                fx['high'] = first_k['high']
                fx['datetime'] = second_k['datetime']
                fx['k1'] = first_k
                fx['k2'] = second_k
                fx['k3'] = third_k

                kdj = self.get_kdj(second_k['datetime'])
                fx['K'] = kdj['K'].iloc[-1]
                fx['D'] = kdj['D'].iloc[-1]
                fx['J'] = kdj['J'].iloc[-1]
                self.fxs.append(fx)

    def get_kdj(self, datetime):
        df = self.klines_orig_df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df[df['datetime'] <= datetime]

        # 计算KDJ指标所需的参数
        n = 9  # 通常KDJ的周期参数为9
        m1 = 3  # K值的平滑参数
        m2 = 3  # D值的平滑参数

        # 计算未成熟随机值RSV
        df['low_n'] = df['low'].rolling(window=n, min_periods=1).min()
        df['high_n'] = df['high'].rolling(window=n, min_periods=1).max()
        df['RSV'] = (df['close'] - df['low_n']) / (df['high_n'] - df['low_n']) * 100

        # 计算K值和D值
        df['K'] = df['RSV'].ewm(alpha=1 / m1, adjust=False).mean()
        df['D'] = df['K'].ewm(alpha=1 / m2, adjust=False).mean()

        # 计算J值
        df['J'] = 3 * df['K'] - 2 * df['D']
        return df

    '''
    合并
    '''

    def merge(self):
        """
        docstring
        """
        if len(self.klines_orig) <= 2:
            self.klines_merge = self.klines_orig
            return
        direct = "unknown"
        for i in range(len(self.klines_orig)):
            current_kline = self.klines_orig[i]
            if len(self.klines_merge) < 3:
                # 为了防止开始的K线合并，所以去掉合并的K线再进行
                if len(self.klines_merge) > 0:
                    second_kline = self.klines_merge[-1]
                    if (current_kline['low'] <= second_kline['low'] and current_kline['high'] >= second_kline['high']) or \
                            (current_kline['low'] >= second_kline['low'] and current_kline['high'] <= second_kline['high']):
                        continue

                self.klines_merge.append(current_kline)
            else:
                first_kline = self.klines_merge[-2]
                second_kline = self.klines_merge[-1]
                if first_kline['high'] < second_kline['high'] and first_kline['low'] < second_kline['low']:
                    direct = "up"
                if first_kline['high'] > second_kline['high'] and first_kline['low'] > second_kline['low']:
                    direct = "down"
                if direct == "unknown":
                    print("error direct")
                    continue
                if (current_kline['low'] <= second_kline['low'] and current_kline['high'] >= second_kline['high']) or \
                        (current_kline['low'] >= second_kline['low'] and current_kline['high'] <= second_kline['high']):
                    if direct == 'up':
                        maxhigh = max(current_kline['high'], second_kline['high'])
                        maxlow = max(current_kline['low'], second_kline['low'])
                        second_kline['high'] = maxhigh
                        second_kline['low'] = maxlow
                    if direct == "down":
                        minhigh = min(current_kline['high'], second_kline['high'])
                        minlow = min(current_kline['low'], second_kline['low'])
                        second_kline['high'] = minhigh
                        second_kline['low'] = minlow
                else:
                    self.klines_merge.append(current_kline)

    '''
    底分型买点
    '''

    def get_lastest_bottom_fx(self):
        fx_count = len(self.fxs)
        if fx_count > 0:
            fx_tail = self.fxs[-1]
            if fx_tail['mark'] == 'l':
                return fx_tail
        return None

    '''
    顶分型卖点
    '''

    def get_lastest_top_fx(self):
        fx_count = len(self.fxs)
        if fx_count > 0:
            fx_tail = self.fxs[-1]
            if fx_tail['mark'] == 'h':
                return fx_tail
        return None

    '''
    强底分型：第三根k线最高价大于第一根k线的最高价
    '''

    def get_strong_bottom_fx(self):
        fx_tail = self.get_lastest_bottom_fx()
        if fx_tail:
            if fx_tail['k3']['high'] >= fx_tail['k1']['high']:
                return fx_tail
        return None

    '''
    强顶分型：第三根k线最底价小于第一根k线的最底价
    '''

    def get_strong_top_fx(self):
        fx_tail = self.get_lastest_top_fx()
        if fx_tail:
            if fx_tail['k3']['low'] >= fx_tail['k1']['low']:
                return fx_tail
        return None

    '''
    笔三买判断
    hub_direct：中枢趋势方向
    hub_layer：中枢的层数, 0代表忽略，1代表第一层中枢，2代表第二层中枢，以此类推
    '''

    # direct is up or down
    def get_lastest_hub(self, hub_direct='up', hub_layer=0):
        hub_count = len(self.hubs)
        if hub_count > 0:
            hub_tail = self.hubs[-1]
            if hub_tail['mark'] == hub_direct:
                if hub_layer == 0:
                    return hub_tail
                elif hub_tail['layer'] == hub_layer:
                    return hub_tail
        return None


if __name__ == "__main__":

    '''
    数据格式
    {'datetime': '2023-08-10 10:00:00', 'code': 'sz.000001', 'open': 16.56, 'high': 17.37, 
    'low': 16.54, 'close': 17.1, 'volume': 209561419,}
    '''
    symbol = "000001"
    start_datetime = datetime(1999, 8, 31, 11, 15, 0)
    end_datetime = datetime(2099, 9, 5, 11, 15, 0)
    # start_datetime = datetime(2009, 7, 8, 0, 0, 0)
    # end_datetime = datetime(2012, 7, 20, 0, 0, 0)


    klines_h = pd.read_csv("./" + symbol + "_1d.csv")
    klines_h['datetime'] = pd.to_datetime(klines_h['datetime'])
    # 使用布尔索引来筛选出'datetime'列小于今天的所有行
    klines_h = klines_h[(klines_h['datetime'] <= end_datetime) & (klines_h['datetime'] >= start_datetime)]
    klines_h = klines_h.sort_values('datetime')
    klines_h['code'] = symbol
    klines_h.set_index('datetime', inplace=True)
    klines_h = klines_h.reset_index()

    if len(klines_h) > 0:
        chan_h = ChanLun(klines_h)
        hub_tail = chan_h.get_lastest_hub(hub_direct='up', hub_layer=0)
        print('hub_tail', hub_tail)
        print('is_in_hub', chan_h.is_in_hub)
        # if bthird_buy:
        # print(chan_h.fbs)
        # print(chan_h.hubs)
        chan_h.draw(symbol)
        # print(price)
