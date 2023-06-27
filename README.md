### 数据格式转换工具
将不同的轨迹数据, 利用配置文件指定字段的对应映射关系, 从一种格式转换为内部标准格式.

#### 步骤 1: 准备数据
首先, 准备需要转换的数据文件. 可以将数据文件放在单独的文件夹中, 以便用于转换. 

#### 步骤 2: 编辑配置文件
打开 config.ini 配置文件, 并编辑需要转换的数据格式和目标格式. 在 input 部分设置输入数据的路径和格式, 在 output 部分设置转换后数据的路径和格式. 示例配置文件: 

* 设置输入数据格式
    在本配置文件中, 你需要设置输入数据的格式. 在 [FileType] 一节中进行设置, 例如: 
    ```
    [FileType]
    type = csv
    ``` 

* 配置Json设置
    如果 FileType 的类型设置为 json , 则通过配置 [Json] 一节来指定 pandas.json_normalize() 方法中的 record_path 和 meta 两个关键参数. 例如, 以下是 json 格式的示例配置:       
    ```
    [Json]
    record_path = ['data', 'rsms', 'participants']
    meta = [['data', 'timestamp'], ['data', 'rsms', 'refPos', 'lon'],['data', 'rsms', 'refPos', 'lat']]
    ```
    如果 FileType 的类型不是 json , 不需要配置任何内容, [Json] 一节为空即可. 

* 设置常量
    在 [Const] 一节中, 你需要设置常量值. 例如, 以下是示例代码: 
    ```
    [Const]
    OriginLat = 23.023899623618
    OriginLon = 113.488177461743
    ```
* 设置标准格式的列名及其对应关系
    在 [ColumnSettings] 一节中, 设置需要输出的列名称、对应关系. 例如:       
    `=` 左边是标准格式的所有的列名,一共 21 列.      
    `=` 右边是标准格式对应的列名, 需要对这些列进行转换. 如果原始数据中没有与标准格式对应的列名, 设为None.
    ```
    [ColumnSettings]
    ID = ptcId
    Time = data.timestamp
    PositionX = pos.lat
    PositionY = pos.lon
    PositionZ = None
    Length = size.length
    Width = size.width
    Height = size.height
    Yaw = heading
    Pitch = None
    Roll = None
    VX = speed
    VY = speed
    VZ = None
    AX = None
    AY = None
    AZ = None
    Category = ptcType
    Style = None
    Color = vehicleColor
    Ego = None
    ```
* 设置转化规则
    `=` 左边是标准格式的列名.     
    `=` 右边是转化为标准格式列, 需要进行转换的操作.            
    在 [SeriesRules] 一节中, 设置数据在转换过程中，只涉及到自身列时需要使用的 lambda 规则. 例如: 
    ```
    [SeriesRules]
    Time = lambda x: x / 1000
    Length = lambda x: x / 100
    Width = lambda x: x / 100
    Height = lambda x: x / 100
    Yaw = lambda x: (90.0 - x * 0.0125) %% 360.0
    ID = lambda x: x
    Category = lambda x: {0:'unknown', 1:'motor', 2:'non-motor', 3:'pedestrian', 4:'rsu'}.get(x,x)
    Color = lambda x: {0:'white',1:'gray',3:'yellow',4:'pink',5:'purple',6:'green',7:'blue',8:'red',9:'brown',10:'orange',11:'black'}.get(x,x)
    ```
    
    在 [DataframeRules] 一节中, 设置数据在转换过程中，涉及到多列时需要使用的 lambda 规则. 例如: 
    ```
    [DataframeRules]
    VX = lambda x: x['speed'] * 0.02 * math.cos(math.radians(x['heading']))
    VY = lambda x: x['speed'] * 0.02 * math.sin(math.radians(x['heading']))
    Ego = lambda x: 'Y' if x['ptcId'] == 0 else 'N'
    PositionX, PositionY, PositionZ = lambda x: pymap3d.geodetic2enu(x['pos.lat'], x['pos.lon'], 0.0, ${Const:OriginLat}, ${Const:OriginLon}, 0.0)
    ```

#### 步骤 3: 运行转换
在编辑好配置文件后, 运行转换程序. 使用命令行运行, 例如: 
```
python translate.py --config-file <path-to-config-file> --input-file <path-to-input-file> --output-file <path-to-output-file>
```      
运行程序后, 程序将自动读取配置文件, 将输入数据文件转换为目标格式, 并将结果写入输出文件.

#### 步骤 4: 检查结果
转换完成后, 检查输出文件是否是正确的格式和内容, 以确保转换成功. 

### 注意事项: 
* 确保输入数据文件和输出数据文件存在.         
* 配置文件中的 [ColumnSettings] 列名对应关系以及 [SeriesRules], [DataframeRules] 节中的规则需要与实际数据格式相匹配.  
* 转换后的文件都是csv文件.
* 支持转化的文件类型有: csv, excel, txt, json.
