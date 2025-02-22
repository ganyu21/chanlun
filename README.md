# chanlun
## 缠论分型、笔和中枢实现
轻量级的缠论实现，只依赖一些简单的库。

首先需要python3.9及以上

然后运行
```
pip install -r requirements.txt
```

接着修改main方法里面symbol、start_datetime和end_datetime。
symbol是股票代码，需要在同级目录有对应的股票代码csv行情文件，格式为
```
datetime,open,high,low,close,volume
```

最后运行
```
python chan.py
```

自动启动浏览器，对指定symbol进行查看可视化分型、笔和中枢。

欢迎大家在此基础上继续实现线段、线段生成的中枢。

