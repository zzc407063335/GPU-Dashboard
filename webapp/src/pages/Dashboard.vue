<template>
  <div>
    <!--Stats cards-->
    <div class="row">
      <div class="col-md-6 col-xl-3" v-for="stats in statscardsData" :key="stats.title">
        <stats-card>
          <div class="icon-big text-center" :class="`icon-${stats.type}`" slot="header">
            <i :class="stats.icon"></i>
          </div>
          <div class="numbers" slot="content">
            <p>{{stats.title}}</p>
            {{stats.value}}
          </div>
          <div class="stats" slot="footer">
            <i :class="stats.footerIcon"></i> {{stats.footerText}}
          </div>
        </stats-card>
      </div>
    </div>
    <!-- Table Info -->
    <div class="row">

        <div class="col-12">
          <card :title="'设备信息总览'" :subTitle="'详情'">
            <div slot="raw-content" class="table-responsive">
              <paper-table :data="tableData" :columns="tableColumns">

              </paper-table>
            </div>
          </card>
        </div>
    </div>
    <!--Charts-->
    <div class="row">
      <div class="col-md-6 col-12">
          <div class="card">
            <div class="card-header" >
                <h4 class="card-title">GPU 使用情况</h4>
            </div>
            <div  class="card-body">
                <ve-line style="width: auto; height: 350px; position: relative;" :data="usagerateData" :settings="chartSettings" :extend="chartExtend" :colors="usagecolors"></ve-line>
                <div class="footer">
                  <div class="stats text-center">
                      <span><i class="ti-reload"></i> 30s刷新 </span>
                  </div>
                </div>
            </div>
          </div>
      </div>
      <div class="col-md-6 col-12">
          <div class="card">
            <div class="card-header" >
                <h4 class="card-title">风扇转速</h4>
            </div>
            <div  class="card-body">
              <ve-line style="width: auto; height: 350px; position: relative;" :colors="fancolors" :data="fanData" :settings="chartSettings" :extend="chartExtend"></ve-line>
              <div class="footer">
                <div class="stats text-center">
                    <span><i class="ti-reload"></i> 30s刷新 </span>
                </div>
              </div>
            </div>
          </div>
      </div>
      <div class="col-md-6 col-12">
          <div class="card">
            <div class="card-header" >
                <h4 class="card-title">风扇转速</h4>
            </div>
            <div  class="card-body">
              <ve-line style="width: auto; height: 350px; position: relative;" :colors="tempcolors" :data="fanData" :settings="chartSettings" :extend="chartExtend"></ve-line>
              <div class="footer">
                <div class="stats text-center">
                    <span><i class="ti-reload"></i> 30s刷新 </span>
                </div>
              </div>
            </div>
          </div>
      </div>
      <div class="col-md-6 col-12">
          <div class="card">
            <div class="card-header" >
                <h4 class="card-title">风扇转速</h4>
            </div>
            <div  class="card-body">
              <ve-line style="width: auto; height: 350px; position: relative;" :colors="powercolors" :data="fanData" :settings="chartSettings" :extend="chartExtend"></ve-line>
              <div class="footer">
                <div class="stats text-center">
                    <span><i class="ti-reload"></i> 30s刷新 </span>
                </div>
              </div>
            </div>
          </div>
      </div>
    </div>
    <!-- Memory usage -->
    <div class="row">
      <div class="col-md-6 col-12" v-for="mem in memData" :key="mem.id">
        <div class="card">
          <div class="card-header" >
              <h4 class="card-title text-center">GPU {{mem.id}} 使用情况</h4>
          </div>
          <div  class="card-body">
            <ve-gauge style="width: auto; height: 350px; position: relative;" :data="mem.pieData" :settings="pieSettings"></ve-gauge>
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-12">
        <card :title=processTable.title :subTitle=processTable.subTitle>
          <div slot="raw-content" class="table-responsive">
            <paper-table :data="processTable.data" :columns="processTable.columns">
            </paper-table>
          </div>
        </card>
      </div>

    </div>
  </div>
</template>
<script>
import { PaperTable,StatsCard, ChartCard } from "@/components/index";
import VeLine from 'v-charts/lib/line.common'
import VeGauge from 'v-charts/lib/gauge.common'
import Chartist from 'chartist';
const tableColumns = ["PID", "进程名", "内存占用", "设备编号"];
const tableData = [
  {
    pid: 1,
    进程名: "python",
    内存占用: "$36.738",
    设备编号: "Niger",
  },
  {
    pid: 2,
    进程名: "python",
    内存占用: "$23,789",
    设备编号: "Curaçao",
  },
  {
    pid: 3,
    进程名: "python",
    内存占用: "$56,142",
    设备编号: "Netherlands",
  },
  {
    pid: 4,
    进程名: "python",
    内存占用: "$38,735",
    设备编号: "Korea, South",
  },
  {
    pid: 5,
    进程名: "python",
    内存占用: "$63,542",
    设备编号: "Malawi",
  }
];
export default {
  components: {
    VeGauge,
    VeLine,
    StatsCard,
    ChartCard,
    PaperTable
  },
  /**
   * Chart data used to render stats, charts. Should be replaced with server data
   */
  data() {
    this.usagecolors = ['#c23531', '#2f4554', '#61a0a8',
        '#d48265', '#91c7ae','#749f83',
        '#ca8622', '#bda29a','#6e7074',
        '#546570', '#c4ccd3'
    ]
    this.fancolors = ['#546570','#bda29a','#c4ccd3','#c23531', '#2f4554', '#61a0a8','#d48265',
         '#91c7ae','#749f83','#ca8622','#6e7074'
    ]
    this.tempcolors = ['#546570','#bda29a','#c4ccd3','#c23531', '#2f4554', '#61a0a8','#d48265',
         '#91c7ae','#749f83','#ca8622','#6e7074'
    ]
    this.powercolors = ['#546570','#bda29a','#c4ccd3','#c23531', '#2f4554', '#61a0a8','#d48265',
         '#91c7ae','#749f83','#ca8622','#6e7074'
    ]
    this.chartSettings =  {
      yAxisType: ['percent'],
      area: true
    }
    this.chartExtend= {
        'yAxis.0.min': 0, // yAxis.0：y轴左侧 //设置纵坐标的最小值
        'yAxis.0.max': 1, // 设置纵坐标的最大值
        'yAxis.0.minInterval': 0.2, // minInterval设置间隔值，1为整数
        'yAxis.1.splitLine.show': false,// yAxis.1： y轴右侧 //不显示值标线
        'yAxis.1.minInterval': 25, // minInterval设置间隔值，1为整数
        'xAxis.0.show': false
     }
    this.pieSettings={
        dataName: {
          '占比': '内存使用率'
        },
        dataType: {
          '占比': 'percent'
        },
        seriesMap: {
          '占比': {
            min: 0,
            max: 1
          }
        }
    }
    return {
      processTable: {
        title: "进程查看",
        subTitle: "每个设备运行进程查看",
        columns: [...tableColumns],
        data: [...tableData]
      },
      usagerateData: {
          columns: ['时间', 'GPU 0', 'GPU 1'],
          rows: [
            { '时间': '15:08', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:09', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:10', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:11', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:12', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:13', 'GPU 0': 0, 'GPU 1': 0}
          ]
        },

       tableColumns: ["设备编号", "设备名称", "产品系列", "内存大小", "设定功率"],
       tableData: [
            {
              "设备编号": 0,
              "设备名称": "NVIDIA RTX 2080Ti",
               "产品系列": "RTX",
              "内存大小": "11 GB",
              "设定功率": "250W"
            },
            {
              "设备编号": 1,
              "设备名称": "NVIDIA RTX 2080Ti",
               "产品系列": "RTX",
              "内存大小": "11 GB",
              "设定功率": "250W"
            }
      ],
      fanData: {
          columns: ['时间', 'GPU 0', 'GPU 1'],
          rows: [
            { '时间': '15:08', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:09', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:10', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:11', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:12', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:13', 'GPU 0': 0, 'GPU 1': 0}
          ]
        },

       tableColumns: ["设备编号", "设备名称", "产品系列", "内存大小", "设定功率"],
       tableData: [
            {
              "设备编号": 0,
              "设备名称": "NVIDIA RTX 2080Ti",
               "产品系列": "RTX",
              "内存大小": "11 GB",
              "设定功率": "250W"
            },
            {
              "设备编号": 1,
              "设备名称": "NVIDIA RTX 2080Ti",
               "产品系列": "RTX",
              "内存大小": "11 GB",
              "设定功率": "250W"
            }
      ],
      statscardsData: [
        {
          type: "warning",
          icon: "ti-desktop",
          title: "设备数量",
          value: "2",
          footerText: "刷新",
          footerIcon: "ti-reload"
        },
        {
          type: "success",
          icon: "ti-server",
          title: "内存总量",
          value: "22 GB",
          footerText: "固定",
          footerIcon: "ti-calendar"
        },
        {
          type: "danger",
          icon: "ti-layout-accordion-merged",
          title: "任务数量",
          value: "23",
          footerText: "正在进行",
          footerIcon: "ti-timer"
        },
        {
          type: "info",
          icon: "ti-search",
          title: "设备状况",
          value: "正常",
          footerText: "更新",
          footerIcon: "ti-reload"
        }
      ],
      memData: [
        {
          id:'1',
          pieData:{
            columns: ['type', 'value'],
            rows: [
            { type: '占比', value: 0.1 }
            ]
          }
        },
        {
          id:'2',
          pieData:{
            columns: ['type', 'value'],
            rows: [
            { type: '占比', value: 0.3 }
            ]
          }
        },
        {
          id:'3',
          pieData:{
            columns: ['type', 'value'],
            rows: [
            { type: '占比', value: 0.3 }
            ]
          }
        },
        {
          id:'4',
          pieData:{
            columns: ['type', 'value'],
            rows: [
            { type: '占比', value: 0.4 }
            ]
          }
        }
      ],
      tempData:{
          columns: ['时间', 'GPU 0', 'GPU 1'],
          rows: [
            { '时间': '15:08', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:09', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:10', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:11', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:12', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:13', 'GPU 0': 0, 'GPU 1': 0}
          ]
      },
      powerData:{
          columns: ['时间', 'GPU 0', 'GPU 1'],
          rows: [
            { '时间': '15:08', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:09', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:10', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:11', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:12', 'GPU 0': 0, 'GPU 1': 0},
            { '时间': '15:13', 'GPU 0': 0, 'GPU 1': 0}
          ]
        }
    };
  },
  methods: {
      getData() {
        var axisData = (new Date()).toLocaleTimeString().replace(/^\D*/,'')
        var len = this.usagerateData.rows.length
        var data_nex = []
        for (var i = 0; i < len - 1; i++) {
            this.usagerateData.rows[i]['GPU 0'] = this.usagerateData.rows[i + 1]['GPU 0']
        }
        this.usagerateData.rows[len - 1]['GPU 0'] = Math.random()
        var data_new = this.usagerateData['GPU 0']
        for (let mem of this.memData) {
            console.log(mem.pieData.rows[0].value = Math.random().toFixed(2));
        }
        console.log(axisData);
      },
            // 这是一个定时器
    timer() {
          return setInterval(()=>{
              this.getData()
          },1000)
    }
  },
  mounted() {
      console.log("加载完成")
      this.getData()
  },
  created() {
      console.log("创建完成")
      // this.getData()
  },
  activated(){
      this.timer_id = this.timer()

      console.log("重新载入")
  },
  deactivated() {
      console.log("缓存起来")
      clearInterval(this.timer_id)
  },
  beforeDestroy() {
      console.log("销毁")
      clearInterval(this.timer_id)
  }
}
</script>
<style>
</style>
