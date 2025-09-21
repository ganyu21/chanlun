
import pandas as pd

from pyecharts.charts import Kline, Bar
from pyecharts import options as opts
import webbrowser

import os
from datetime import datetime, timedelta

'''
缠中说禅分析
'''


class ChanLun:

    def __init__(self, klines, symbol="mystock"):
        self.symbol = symbol
        self.klines_orig_df = klines  # 原始K线, dataframe格式
        self.klines_orig = klines.to_dict(orient='records')  # 原始K线, list格式
        self.klines_merge = []  # 合并后的K线
        self.fxs = []  # 分型
        self.pens = []  # 笔列表
        self.hubs = []  # 中枢列表
        self.status = "未确定"
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

    def split_data_for_third_points(self):
        """
        获取第三买卖点的数据，用于在图表中标记
        """
        mark_point_data = []
        for hub in self.hubs:
            # 检查第三买点
            if hub.get('third_buy_datetime') and hub.get('third_buy_price'):
                mark_point_data.append({
                    "coord": [hub['third_buy_datetime'], hub['third_buy_price']],
                    "name": "第三买点",
                    "symbol": "arrow",
                    "symbolSize": 15,
                    "itemStyle": {"color": "red"},
                    "label": {"show": True, "color": "red", "fontSize": 12}
                })
            # 检查第三卖点
            if hub.get('third_sell_datetime') and hub.get('third_sell_price'):
                mark_point_data.append({
                    "coord": [hub['third_sell_datetime'], hub['third_sell_price']],
                    "name": "第三卖点",
                    "symbol": "triangle",
                    "symbolSize": 15,
                    "itemStyle": {"color": "green"},
                    "label": {"show": True, "color": "green", "fontSize": 12}
                })
        return mark_point_data

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

        # 获取第三买卖点数据
        third_points_data = self.split_data_for_third_points()

        kline = (
            Kline().add_xaxis(ktime).add_yaxis(series_name=self.symbol, y_axis=kdata,
                                               markline_opts=opts.MarkLineOpts(
                                                   label_opts=opts.LabelOpts(position="middle", color="blue", font_size=15),
                                                   symbol="none",  # 去除连线两端的箭头
                                                   data=self.split_data_for_kline()),
                                               markpoint_opts=opts.MarkPointOpts(
                                                   data=third_points_data,
                                                   label_opts=opts.LabelOpts(
                                                       font_size=12,
                                                       font_weight="bold",
                                                       color="white"
                                                   )
                                               )
                                               )
            .set_global_opts(xaxis_opts=opts.AxisOpts(is_scale=True),
                             yaxis_opts=opts.AxisOpts(is_scale=True,
                                                      splitarea_opts=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)),
                                                      ),
                             datazoom_opts=[opts.DataZoomOpts(range_start=0, range_end=100)],
                             title_opts=opts.TitleOpts(title=self.symbol),
                             )
            .set_series_opts(
                markarea_opts=opts.MarkAreaOpts(is_silent=True, data=self.split_data_for_hub())
            )
        )

        bar = (Bar().add_xaxis(ktime).add_yaxis("", kvol))
        path = f"{os.path.expanduser('~/Downloads/')}/quant/" + self.symbol + "-" + freq + ".html"
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
        for i in range(len(self.klines_merge)):
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
    {'start_datetime': Timestamp('2024-02-23 00:00:00'), 'low_price': 9.35, 'high_price': 9.79, 'end_datetime': Timestamp('2024-04-12 00:00:00'), 'signal_price': 9.85, 'signal_datetime': Timestamp('2024-05-15 00:00:00'), 'mark': 'up', 'layer': 1, 'finish':'yes'}
    '''

    def kline_hub(self):
        """
        根据缠论标准定义计算中枢：
        某级别走势类型中，被至少三个连续的次级别走势类型所重叠的部分
        中枢 = 三段连续走势的重叠区间 + 后续扩展
        注意：三段走势需要4个分型（即至少需要4笔）
        """
        pen_len = len(self.pens)
        if pen_len < 4:  # 至少需要4笔才能构成三段走势
            return

        i = 0
        up_layer = 0
        down_layer = 0

        while i <= pen_len - 4:  # 需要4笔构成三段走势
            # 尝试从当前位置构建三段走势的中枢
            if i + 3 < pen_len:
                # 获取三段连续走势的价格区间
                # 第一段走势：第i笔到第i+1笔
                segment1_high, segment1_low = self._get_segment_range(i, i + 1)
                # 第二段走势：第i+1笔到第i+2笔
                segment2_high, segment2_low = self._get_segment_range(i + 1, i + 2)
                # 第三段走势：第i+2笔到第i+3笔
                segment3_high, segment3_low = self._get_segment_range(i + 2, i + 3)

                # 检查是否有有效的段信息
                if (segment1_high is None or segment2_high is None or segment3_high is None or 
                    segment1_low is None or segment2_low is None or segment3_low is None):
                    i += 1
                    continue

                # 计算三段走势的重叠区间
                overlap_high = min(segment1_high, segment2_high, segment3_high)
                overlap_low = max(segment1_low, segment2_low, segment3_low)

                # 检查是否有有效重叠（构成中枢的必要条件）
                if overlap_low < overlap_high:
                    # 构建中枢
                    hub = {
                        'start_datetime': self.pens[i]['fx']['k2']['datetime'],
                        'low_price': overlap_low,
                        'high_price': overlap_high,
                        'finish': 'no',
                        'mark': self._determine_hub_trend(i, i + 3)
                    }

                    # 寻找中枢扩展：检查后续走势是否与中枢重叠
                    j = 4  # 从第5笔开始检查扩展
                    last_in_hub = i + 3  # 记录最后一个在中枢内的笔

                    while i + j < pen_len:
                        # 检查第i+j-1笔到第i+j笔的走势是否与中枢重叠
                        segment_high, segment_low = self._get_segment_range(i + j - 1, i + j)
                        if segment_high is None or segment_low is None:
                            break

                        # 检查当前走势是否与中枢重叠
                        if segment_low < hub['high_price'] and segment_high > hub['low_price']:
                            # 有重叠，中枢扩展
                            # 不需要改变中枢区间，因为中枢的上下沿由初始三段确定
                            last_in_hub = i + j
                            j += 1
                        else:
                            # 无重叠，中枢结束
                            break

                    # 设置中枢结束时间
                    hub['end_datetime'] = self.pens[last_in_hub]['fx']['k2']['datetime']

                    # 寻找第三类买卖点：中枢结束后的突破点（仅对已完成的中枢）
                    if True:  # 始终尝试寻找第三类买卖点
                        third_point_info = self._find_third_point(hub, i + j, pen_len)
                        if third_point_info['third_buy_info']:
                            # 添加专门的第三买点和第三卖点字段
                            hub['third_buy_price'] = third_point_info['third_buy_info']['price']
                            hub['third_buy_datetime'] = third_point_info['third_buy_info']['datetime']
                        if third_point_info['third_sell_info']:
                            hub['third_sell_price'] = third_point_info['third_sell_info']['price']
                            hub['third_sell_datetime'] = third_point_info['third_sell_info']['datetime']
                        hub['finish'] = 'yes' if third_point_info['third_buy_info'] or third_point_info['third_sell_info'] else 'no'

                    # 设置中枢层级
                    if hub['mark'] == 'up':
                        if down_layer == 0:
                            up_layer += 1
                            hub['layer'] = up_layer
                        else:
                            down_layer = 0
                            up_layer = 1
                            hub['layer'] = up_layer
                    else:  # 'down'
                        if up_layer == 0:
                            down_layer += 1
                            hub['layer'] = down_layer
                        else:
                            up_layer = 0
                            down_layer = 1
                            hub['layer'] = down_layer

                    # 只添加已完成的中枢或第一个未完成的中枢
                    if hub['finish'] == 'yes' or (len(self.hubs) == 0 or self.hubs[-1]['finish'] == 'yes'):
                        self.hubs.append(hub)

                    # 跳过已处理的笔
                    i = last_in_hub
                else:
                    i += 1
            else:
                i += 1

    def _find_third_point(self, hub, start_pen_idx, pen_len):
        """
        寻找第三类买卖点：中枢结束后的转折点
        第三类买点：中枢结束后的第一个底分型
        第三类卖点：中枢结束后的第一个顶分型
        返回：包含third_buy_info和third_sell_info的字典
        """
        if start_pen_idx >= pen_len:
            return {'third_buy_info': None, 'third_sell_info': None}

        hub_high = hub['high_price']
        hub_low = hub['low_price']
        hub_mark = hub['mark']  # 获取中枢趋势方向

        # 记录找到的顶分型和底分型数量
        third_buy_info = None
        third_sell_info = None

        # 从中枢结束后的第一个笔开始扫描，寻找第三类买卖点
        for i in range(start_pen_idx, pen_len):
            current_pen = self.pens[i]
            pen_price = current_pen['price']
            pen_mark = current_pen['fx']['mark']

            # 根据中枢趋势方向确定第三类买卖点的寻找逻辑
            if hub_mark == 'up':  # 向上趋势的中枢
                # 寻找底分型作为第三买点
                if pen_mark == 'l':
                    if pen_price > hub_high:  # 底分型高于中枢上沿，确认为第三买点
                        # 这是第一个底分型，作为第三买点
                        if third_buy_info is None:  # 只记录第一个
                            third_buy_info = {
                                'price': pen_price,
                                'datetime': current_pen['fx']['k2']['datetime'],
                                'type': 'buy',
                                'pen_index': i
                            }
                # 寻找顶分型作为第三卖点
                if pen_mark == 'h':
                    # 检查顶分型是否高于中枢上沿（突破后形成的顶分型）
                    if pen_price > hub_high:
                        # 第一个顶分型作为第三卖点
                        if third_sell_info is None:  # 只记录第一个
                            third_sell_info = {
                                'price': pen_price,
                                'datetime': current_pen['fx']['k2']['datetime'],
                                'type': 'sell',
                                'pen_index': i
                            }
            else:  # 向下趋势的中枢
                # 寻找顶分型作为第三卖点
                if pen_mark == 'h':
                    if pen_price < hub_low:  # 顶分型低于中枢下沿，确认为第三卖点
                        # 这是第一个顶分型，作为第三卖点
                        if third_sell_info is None:  # 只记录第一个
                            third_sell_info = {
                                'price': pen_price,
                                'datetime': current_pen['fx']['k2']['datetime'],
                                'type': 'sell',
                                'pen_index': i
                            }
                # 寻找底分型作为第三买点
                if pen_mark == 'l':
                    # 检查底分型是否低于中枢下沿（突破后形成的底分型）
                    if pen_price < hub_low:
                        # 第一个底分型作为第三买点
                        if third_buy_info is None:  # 只记录第一个
                            third_buy_info = {
                                'price': pen_price,
                                'datetime': current_pen['fx']['k2']['datetime'],
                                'type': 'buy',
                                'pen_index': i
                            }

            # 如果同时找到了第三买点和第三卖点，可以继续寻找直到遍历完成
            # 不再提前返回，确保找到所有可能的点

        # 返回包含两个点信息的字典
        return {
            'third_buy_info': third_buy_info,
            'third_sell_info': third_sell_info
        }

    def _find_first_valid_turn(self, hub, breakout_pen_idx, pen_len, point_type):
        """
        在突破后寻找第一个有效的转折点
        point_type: 'buy' 表示寻找第三类买点，'sell' 表示寻找第三类卖点
        """
        hub_high = hub['high_price']
        hub_low = hub['low_price']

        # 从突破笔的下一个笔开始寻找
        for i in range(breakout_pen_idx + 1, pen_len):
            current_pen = self.pens[i]
            pen_price = current_pen['price']
            pen_mark = current_pen['fx']['mark']

            if point_type == 'buy':
                # 寻找第三类买点：需要底分型且不回到中枢内
                if pen_mark == 'l':
                    if pen_price > hub_high:
                        # 第一个不回到中枢内的底分型，确认为第三类买点
                        return {
                            'price': pen_price,
                            'datetime': current_pen['fx']['k2']['datetime'],
                            'type': 'buy',
                            'pen_index': i
                        }
                    else:
                        # 底分型回到中枢内，突破失效，返回None让上层继续寻找下一个突破
                        return None
                # 如果遇到顶分型且回到中枢内，也表示突破失效
                elif pen_mark == 'h' and pen_price <= hub_high:
                    return None

            elif point_type == 'sell':
                # 寻找第三类卖点：需要顶分型且不回到中枢内
                if pen_mark == 'h':
                    if pen_price < hub_low:
                        # 第一个不回到中枢内的顶分型，确认为第三类卖点
                        return {
                            'price': pen_price,
                            'datetime': current_pen['fx']['k2']['datetime'],
                            'type': 'sell',
                            'pen_index': i
                        }
                    else:
                        # 顶分型回到中枢内，突破失效，返回None让上层继续寻找下一个突破
                        return None
                # 如果遇到底分型且回到中枢内，也表示突破失效
                elif pen_mark == 'l' and pen_price >= hub_low:
                    return None

        # 没有找到符合条件的转折点
        return None

    def _get_segment_range(self, pen_start_idx, pen_end_idx):
        """
        获取走势段的价格区间
        走势段是从一个分型到下一个相反分型的价格运动轨迹
        """
        if pen_start_idx >= len(self.pens) or pen_end_idx >= len(self.pens):
            return None, None

        start_pen = self.pens[pen_start_idx]
        end_pen = self.pens[pen_end_idx]

        # 走势段的起点：起始笔的分型极值
        if start_pen['fx']['mark'] == 'h':  # 顶分型
            start_price = start_pen['fx']['k2']['high']
        else:  # 底分型
            start_price = start_pen['fx']['k2']['low']

        # 走势段的终点：结束笔的分型极值
        if end_pen['fx']['mark'] == 'h':  # 顶分型
            end_price = end_pen['fx']['k2']['high']
        else:  # 底分型
            end_price = end_pen['fx']['k2']['low']

        # 走势段的价格区间
        segment_high = max(start_price, end_price)
        segment_low = min(start_price, end_price)

        return segment_high, segment_low

    def _get_pen_range(self, pen_index):
        """
        获取笔的价格区间（高点和低点）
        笔是从一个分型连接到下一个分型的线段，价格区间包括这条线段覆盖的所有价格
        """
        if pen_index >= len(self.pens):
            return None, None

        current_pen = self.pens[pen_index]

        # 获取当前笔连接的两个分型
        if pen_index == 0:
            # 第一笔：从初始位置到第一个分型
            # 这里需要特殊处理，因为没有前一个分型
            # 使用第一个分型自身作为起点
            start_fx = current_pen['fx']
            end_fx = current_pen['fx']
        else:
            # 从前一笔的结束分型到当前笔的结束分型
            start_fx = self.pens[pen_index - 1]['fx']
            end_fx = current_pen['fx']

        # 计算笔覆盖的价格区间
        # 起点分型的极值
        if start_fx['mark'] == 'h':  # 顶分型
            start_price = start_fx['k2']['high']
        else:  # 底分型
            start_price = start_fx['k2']['low']

        # 终点分型的极值
        if end_fx['mark'] == 'h':  # 顶分型
            end_price = end_fx['k2']['high']
        else:  # 底分型
            end_price = end_fx['k2']['low']

        # 笔的价格区间是起点和终点价格形成的区间
        pen_high = max(start_price, end_price)
        pen_low = min(start_price, end_price)

        return pen_high, pen_low

    def _determine_hub_trend(self, start_pen, end_pen):
        """
        根据构成中枢的笔段确定中枢趋势方向
        主要基于中枢相对于前一个中枢的价格位置，其次考虑突破方向
        """
        if start_pen >= len(self.pens) or end_pen >= len(self.pens):
            return 'up'

        # 获取中枢的前三段走势构成的中枢区间
        # 第一段走势：第start_pen笔到第start_pen+1笔
        segment1_high, segment1_low = self._get_segment_range(start_pen, start_pen + 1)
        # 第二段走势：第start_pen+1笔到第start_pen+2笔
        segment2_high, segment2_low = self._get_segment_range(start_pen + 1, start_pen + 2)
        # 第三段走势：第start_pen+2笔到第start_pen+3笔
        segment3_high, segment3_low = self._get_segment_range(start_pen + 2, start_pen + 3)

        # 检查是否有有效的段信息
        if (segment1_high is None or segment2_high is None or segment3_high is None or
            segment1_low is None or segment2_low is None or segment3_low is None):
            # 如果无法获取段信息，使用简单的价格比较
            start_price = self.pens[start_pen]['price']
            end_price = self.pens[end_pen]['price']
            return 'up' if end_price > start_price else 'down'

        # 计算中枢区间
        hub_high = min(segment1_high, segment2_high, segment3_high)
        hub_low = max(segment1_low, segment2_low, segment3_low)
        hub_center = (hub_high + hub_low) / 2

        # 检查与前一个中枢的价格关系
        current_hub_index = len(self.hubs)  # 当前正在处理的中枢索引
        if current_hub_index > 0:
            prev_hub = self.hubs[-1]  # 前一个中枢
            prev_hub_center = (prev_hub['high_price'] + prev_hub['low_price']) / 2

            # 基于中枢价格位置判断趋势：
            # 如果当前中枢比前一个中枢价格更高，是向上中枢
            # 如果当前中枢比前一个中枢价格更低，是向下中枢
            if hub_center > prev_hub_center:
                return 'up'
            else:
                return 'down'

        # 如果这是第一个中枢，检查中枢结束后的第一个突破方向
        # 从中枢结束后的第一个笔开始检查
        for i in range(end_pen + 1, len(self.pens)):
            pen = self.pens[i]
            pen_price = pen['price']
            pen_mark = pen['fx']['mark']

            # 检查突破中枢上沿
            if pen_mark == 'h' and pen_price > hub_high:
                return 'up'  # 向上突破，向上中枢
            # 检查突破中枢下沿
            elif pen_mark == 'l' and pen_price < hub_low:
                return 'down'  # 向下突破，向下中枢

            # 限制检查范围，避免过远的笔影响判断
            # 如果连续5个笔都没有明显突破，则停止检查
            if i - end_pen >= 5:
                break

        # 如果没有明显突破，根据中枢的整体走势判断
        # 比较中枢开始和结束时的价格位置
        start_price = self.pens[start_pen]['price']
        end_price = self.pens[end_pen]['price']

        # 如果结束价格高于中枢中心，倾向于向上
        if end_price > hub_center:
            return 'up'
        else:
            return 'down'

    '''
    笔划分，笔包括 开始分型（类型、最低和最高、开始分型的三个点，中间点的时间）、笔类型（up或down）、开始分型中间点的最值价格
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
            # print("fx is less then 2")
            return
        fx_count = len(self.fxs)
        for i in range(fx_count):
            current_fx = self.fxs[i]
            if i == fx_count - 1:
                pass
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
        i = 3
        # for i in range(len(self.klines_merge)):
        while i < len(self.klines_merge):
            if i < 2:
                continue
            if i == len(self.klines_merge) - 4:
                pass
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

                self.fxs.append(fx)
                i = i + 1
            # 底分型
            elif (second_k['low'] < first_k['low'] and second_k['low'] < third_k['low']) and \
                    (second_k['high'] < first_k['high'] and second_k['high'] < third_k['high']):
                fx = {}
                fx['mark'] = 'l'
                fx['low'] = second_k['low']
                fx['high'] = first_k['high']
                fx['datetime'] = second_k['datetime']
                fx['k1'] = first_k
                fx['k2'] = second_k
                fx['k3'] = third_k

                self.fxs.append(fx)
                i = i + 1
            else:
                i = i + 1


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
    得到最近已经形成的中枢
    '''

    def get_lastest_finished_hub(self):
        """
        得到最近已经形成的中枢（已完成状态）
        返回: 最近的已完成中枢，如果不存在则返回None
        """
        for hub in reversed(self.hubs):
            if hub['finish'] == 'yes':
                return hub
        return None

    def get_unfinished_hub(self):
        """
        获取当前未结束的中枢
        返回: 未完成的中枢，如果不存在则返回None
        """
        if len(self.hubs) == 0:
            return None
        hub = self.hubs[-1]
        if hub['finish'] == 'no':
            return hub
        return None

    def is_in_hub(self):
        if len(self.hubs) == 0:
            return None
        hub = self.hubs[-1]
        if hub['finish'] == 'no':
            return hub
        return None

    def get_third_buy_point(self):
        """
        获取第三买点的时间和价格信息
        返回: {
            'datetime': 时间,
            'price': 价格,
            'hub_info': 中枢信息
        }
        """
        hub_tail = self.get_lastest_finished_hub()
        if hub_tail:
            # 检查第三买点
            if hub_tail.get('third_buy_datetime') and hub_tail.get('third_buy_price'):
                return {
                    'datetime': hub_tail['third_buy_datetime'],
                    'price': hub_tail['third_buy_price'],
                    'hub_info': hub_tail
                }
        return None

    def get_third_sell_point(self):
        """
        获取第三卖点的时间和价格信息
        返回: {
            'datetime': 时间,
            'price': 价格,
            'hub_info': 中枢信息
        }
        """
        hub_tail = self.get_lastest_finished_hub()
        if hub_tail:
            # 检查第三卖点
            if hub_tail.get('third_sell_datetime') and hub_tail.get('third_sell_price'):
                return {
                    'datetime': hub_tail['third_sell_datetime'],
                    'price': hub_tail['third_sell_price'],
                    'hub_info': hub_tail
                }
        return None


if __name__ == "__main__":

    '''
    数据格式
    {'datetime': '2023-08-10 10:00:00', 'code': 'sz.000001', 'open': 16.56, 'high': 17.37, 
    'low': 16.54, 'close': 17.1, 'volume': 209561419,}
    '''

    symbol = "000001"

    # 设置时间范围
    start_datetime = datetime(2020, 8, 1, 0, 0, 0)
    end_datetime = datetime(2025, 12, 30, 0, 0, 0)

    klines = pd.read_csv('./' + "stock/" + symbol + "_1d.csv")
    klines['datetime'] = pd.to_datetime(klines['datetime'])
    # 使用布尔索引来筛选出'datetime'列小于今天的所有行
    klines = klines[(klines['datetime'] <= end_datetime) & (klines['datetime'] >= start_datetime)]

    if len(klines) > 0:
        chan = ChanLun(klines, symbol)
        # 得到最近已经形成的指定层数的中枢
        hub_tail = chan.get_lastest_finished_hub()
        print('hub_tail', hub_tail)

        # 获取第三买点
        third_buy_point = chan.get_third_buy_point()
        if third_buy_point:
            print(f'第三买点: ')
            print(f'  时间: {third_buy_point["datetime"]}')
            print(f'  价格: {third_buy_point["price"]}')
        else:
            print('暂无第三买点')

        # 获取第三卖点
        third_sell_point = chan.get_third_sell_point()
        if third_sell_point:
            print(f'第三卖点: ')
            print(f'  时间: {third_sell_point["datetime"]}')
            print(f'  价格: {third_sell_point["price"]}')
        else:
            print('暂无第三卖点')

        # 是否在中枢中
        print("是否在中枢中:", chan.get_unfinished_hub())

        # 显示所有中枢信息
        print(f'\n共找到 {len(chan.hubs)} 个中枢:')
        for i, hub in enumerate(chan.hubs):
            status = "已完成" if hub['finish'] == 'yes' else "未完成"
            signal_info = ""
            # 检查第三买点
            if hub.get('third_buy_datetime') and hub.get('third_buy_price'):
                signal_info = f', 第三买点: {hub["third_buy_datetime"]} @ {hub["third_buy_price"]}'
            # 检查第三卖点（使用if而不是elif，以便同时显示）
            if hub.get('third_sell_datetime') and hub.get('third_sell_price'):
                signal_info += f', 第三卖点: {hub["third_sell_datetime"]} @ {hub["third_sell_price"]}'
            print(f'  中枢{i + 1}: {hub["start_datetime"]} - {hub["end_datetime"]}, '
                  f'价格区间: {hub["low_price"]:.2f} - {hub["high_price"]:.2f}, '
                  f'趋势: {hub["mark"]}, 层级: {hub["layer"]}, 状态: {status}{signal_info}')

        chan.draw(symbol)
