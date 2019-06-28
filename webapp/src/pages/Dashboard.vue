<template>
  <div>
    <!--Stats cards-->
    <div class="row">
      <div class="col-md-6 col-xl-4" v-for="stats in statscardsData" :key="stats.title">
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
      <div class="col-md-6 col-xl-4">
          <div class="card">
            <div class="card-body">
              <div>
                <div class="row">
                   <div class="col-5">
                      <div class="icon-big text-center icon-danger">
                        <i :class="'ti-link'"></i>
                      </div>
                   </div>

                   <div class="col-7 text-center">
                     <p-button round outline block @click.native="notifyVue('top','center')"> {{buttonText}} </p-button>
                   </div>
                </div>
                <hr>

                <h4><p class="category"> 当前间隔: {{intervalTime/1000}}s </p></h4>

                <div class="row">
                  <div class="col-4"><p-button size="sm" round outline block @click.native="notifyVueChangeTime('top','right',5)"> 5s </p-button></div>
                  <div class="col-4"><p-button size="sm" round outline block @click.native="notifyVueChangeTime('top','right',30)"> 30s </p-button></div>
                  <div class="col-4"><p-button size="sm" round outline block @click.native="notifyVueChangeTime('top','right',60)"> 60s </p-button></div>
                </div>
              </div>

            </div>
          </div>
      </div>
      <!-- <div class="col-md-6 col-xl-4">
           <div class="numbers" slot="content">
              <p-button round outline block @click.native="notifyVue('top','center')"> {{buttonText}} </p-button>
            </div>
      </div> -->
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
                <ve-line style="width: auto; height: 350px; position: relative;" :data="usagerateData" :settings="percentChartSettings" :extend="percentChartExtend" :colors="usagecolors"></ve-line>
                <div class="footer">
                  <div class="stats text-center">
                      <span><i class="ti-reload"></i> {{intervalTime/1000}}s 刷新 </span>
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
              <ve-line style="width: auto; height: 350px; position: relative;" :colors="fancolors" :data="fanData" :settings="percentChartSettings" :extend="percentChartExtend"></ve-line>
              <div class="footer">
                <div class="stats text-center">
                    <span><i class="ti-reload"></i> {{intervalTime/1000}}s 刷新 </span>
                </div>
              </div>
            </div>
          </div>
      </div>
      <div class="col-md-6 col-12">
          <div class="card">
            <div class="card-header" >
                <h4 class="card-title">温度(°C)</h4>
            </div>
            <div  class="card-body">
              <ve-line style="width: auto; height: 350px; position: relative;" :colors="tempcolors" :data="tempData" :settings="normolChartSettings" :extend="tempExtend"></ve-line>
              <div class="footer">
                <div class="stats text-center">
                    <span><i class="ti-reload"></i> {{intervalTime/1000}}s 刷新 </span>
                </div>
              </div>
            </div>
          </div>
      </div>
      <div class="col-md-6 col-12">
          <div class="card">
            <div class="card-header" >
                <h4 class="card-title">功率使用(W)</h4>
            </div>
            <div  class="card-body">
              <ve-line style="width: auto; height: 350px; position: relative;" :colors="powercolors" :data="powerData" :settings="normolChartSettings" :extend="powerExtend"></ve-line>
              <div class="footer">
                <div class="stats text-center">
                    <span><i class="ti-reload"></i> {{intervalTime/1000}}s 刷新 </span>
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
  </div>
</template>
<script>
import { PaperTable,StatsCard, ChartCard } from "@/components/index";
import NotificationTemplate from './Notifications/NotificationTemplate';
import VeLine from 'v-charts/lib/line.common'
import VeGauge from 'v-charts/lib/gauge.common'
import Chartist from 'chartist';
import axios from 'axios'
// const queryURL = "http://127.0.0.1:5002/gpuinfo/" //后面需要写入到配置文件
const queryURL = "/gpuinfo/"
export default {
  components: {
    VeGauge,
    VeLine,
    StatsCard,
    // ChartCard,
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
    this.tempcolors = ['#F08080','#8B7355','#00CED1','#FAEBD7', '#2f4554', '#61a0a8','#d48265',
         '#91c7ae','#749f83','#ca8622','#6e7074'
    ]
    this.powercolors = ['#EE6363','#5D478B','#8B8B7A','#8B658B', '#8B8989', '#5CACEE','#B2DFEE',
         '#CFCFCF','#EED2EE','#363636','#AB82FF'
    ]
    this.percentChartSettings =  {
      yAxisType: ['percent'],
      area: true
    }
    this.normolChartSettings =  {
      area: true
    }
    this.percentChartExtend= {
        'yAxis.0.min': 0, // yAxis.0：y轴左侧 //设置纵坐标的最小值
        'yAxis.0.max': 1, // 设置纵坐标的最大值
        'yAxis.0.minInterval': 0.2, // minInterval设置间隔值，1为整数
        'yAxis.1.splitLine.show': false,// yAxis.1： y轴右侧 //不显示值标线
        'yAxis.1.minInterval': 25, // minInterval设置间隔值，1为整数
        'xAxis.0.show': true
     }
    this.tempExtend= {
        'yAxis.0.min': 0, // yAxis.0：y轴左侧 //设置纵坐标的最小值
        'yAxis.0.max': 100, // 设置纵坐标的最大值
        'yAxis.0.minInterval': 10, // minInterval设置间隔值，1为整数
        'yAxis.1.splitLine.show': false,// yAxis.1： y轴右侧 //不显示值标线
        'yAxis.1.minInterval': 25, // minInterval设置间隔值，1为整数
        'xAxis.0.show': true
     }
      this.powerExtend= {
        'yAxis.0.min': 0, // yAxis.0：y轴左侧 //设置纵坐标的最小值
        'yAxis.0.max': 300, // 设置纵坐标的最大值
        'yAxis.0.minInterval': 30, // minInterval设置间隔值，1为整数
        'yAxis.1.splitLine.show': false,// yAxis.1： y轴右侧 //不显示值标线
        'yAxis.1.minInterval': 25, // minInterval设置间隔值，1为整数
        'xAxis.0.show': true
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
      buttonText: "暂停监测",
      intervalTime: 30000,
      usagerateData: {
          columns: ['时间'],
          rows: [
            { '时间': 'NA0'},
            { '时间': 'NA1'},
            { '时间': 'NA2'},
            { '时间': 'NA3'},
            { '时间': 'NA4'},
            { '时间': 'NA5'}
          ]
        },

      tableColumns: ["设备编号", "设备名称", "产品系列", "内存大小", "设定功率","工作状态"],
      tableData: [
      ],
      fanData: {
          columns: ['时间'],
          rows: [
            { '时间': 'NA0'},
            { '时间': 'NA1'},
            { '时间': 'NA2'},
            { '时间': 'NA3'},
            { '时间': 'NA4'},
            { '时间': 'NA5'}
          ]
        },
      statscardsData: [
        {
          type: "warning",
          icon: "ti-desktop",
          title: "设备数量",
          value: "0",
          footerText: "固定",
          footerIcon: "ti-gift"
        },
        {
          type: "success",
          icon: "ti-server",
          title: "内存总量",
          value: 0,
          footerText: "固定",
          footerIcon: "ti-pulse"
        },
      ],
      memData: [
      ],
      tempData: {
          columns: ['时间'],
          rows: [
            { '时间': 'NA0'},
            { '时间': 'NA1'},
            { '时间': 'NA2'},
            { '时间': 'NA3'},
            { '时间': 'NA4'},
            { '时间': 'NA5'}
          ]
      },
      powerData: {
            columns: ['时间'],
            rows: [
              { '时间': 'NA0'},
              { '时间': 'NA1'},
              { '时间': 'NA2'},
              { '时间': 'NA3'},
              { '时间': 'NA4'},
              { '时间': 'NA5'}
            ]
          },
    };
  },
  methods: {
      notifyVueChangeTime(verticalAlign, horizontalAlign, intervalTime) {
          clearInterval(this.timer_id)
          this.timer_id = false
          this.intervalTime = intervalTime * 1000
          this.timer_id = this.timer()
          this.$notify({
            component: NotificationTemplate,
            icon: "ti-drupal",
            horizontalAlign: horizontalAlign,
            verticalAlign: verticalAlign,
            type: "warning"
          });
      },
      notifyVue(verticalAlign, horizontalAlign) {
          if(this.timer_id) {
            this.buttonText="开始监测"
            clearInterval(this.timer_id)
            this.timer_id = false
          } else {
            this.buttonText="暂停监测"
            this.timer_id = this.timer()
          }
          this.$notify({
            component: NotificationTemplate,
            icon: "ti-gift",
            horizontalAlign: horizontalAlign,
            verticalAlign: verticalAlign,
            type: "success"
          });
      },
      async getStaticInfo() {
          var api = "gpu_counts"
          var self = this //指向data内的数据
          await axios.post(queryURL+api,{
          }).then(function (response) {
            self.statscardsData[0].value = response.data['counts'] //设备数量
          })
          .catch(function (error) {
            console.log(error)
          })

          var tempMemTotol = 0
          for (var i = 0; i < self.statscardsData[0].value; i++) {
            //初始化列表
            this.usagerateData.columns.push('GPU ' + i.toString())
            this.fanData.columns.push('GPU ' + i.toString())
            this.tempData.columns.push('GPU ' + i.toString())
            this.powerData.columns.push('GPU ' + i.toString())
            var pieJson = {id:i,pieData:{columns: ['type', 'value'],rows: [{ type: '占比', value: 0 }]}}
            this.memData.push(pieJson)
            for (var j = 0; j < self.usagerateData.rows.length; j++) {
                this.usagerateData.rows[j]['GPU ' + i.toString()] = 0
                this.fanData.rows[j]['GPU ' + i.toString()] = 0
                this.tempData.rows[j]['GPU ' + i.toString()] = 0
                this.powerData.rows[j]['GPU ' + i.toString()] = 0
            }

            api = "gpu_mem"
            var tableJson = {}
            tableJson["设备编号"] = i
            //获取内存信息
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              tempMemTotol += Number(response.data['mem_total'])
              tableJson["内存大小"] = Number(response.data['mem_total']).toFixed(2) + " GB"
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_brand"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              tableJson["产品系列"] =response.data['brand_name']
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_powerinfo"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              tableJson["设定功率"] = response.data['setting_powLimit']
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_name"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              tableJson["设备名称"] = response.data['device_name']
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_perfstate"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              tableJson["工作状态"] = response.data['power_state']
            })
            .catch(function (error) {
              console.log(error)
            })

            self.tableData.push(tableJson)
          }
          self.statscardsData[1].value = tempMemTotol.toFixed(2) + " GB"

      },
      async getData() {
        var self = this
        var axisData = (new Date()).toLocaleTimeString().replace(/^\D*/,'')
        var len = this.usagerateData.rows.length
        for (var i = 0; i < len - 1; i++) {
            for (var j = 0; j < self.statscardsData[0].value; j++) {
              this.usagerateData.rows[i]['GPU ' + j.toString()] = this.usagerateData.rows[i + 1]['GPU ' + j.toString()]
              this.usagerateData.rows[i]['时间'] = this.usagerateData.rows[i + 1]['时间']
              this.fanData.rows[i]['GPU ' + j.toString()] = this.fanData.rows[i + 1]['GPU ' + j.toString()]
              this.fanData.rows[i]['时间'] = this.fanData.rows[i + 1]['时间']
              this.tempData.rows[i]['GPU ' + j.toString()] = this.tempData.rows[i + 1]['GPU ' + j.toString()]
              this.tempData.rows[i]['时间'] = this.tempData.rows[i + 1]['时间']
              this.powerData.rows[i]['GPU ' + j.toString()] = this.powerData.rows[i + 1]['GPU ' + j.toString()]
              this.powerData.rows[i]['时间'] = this.powerData.rows[i + 1]['时间']
            }
        }
        this.usagerateData.rows[len - 1]['时间'] = axisData
        this.fanData.rows[len - 1]['时间'] = axisData
        this.tempData.rows[len - 1]['时间'] = axisData
        this.powerData.rows[len - 1]['时间'] = axisData
        var api
        try{
        for (var i = 0; i < self.statscardsData[0].value; i++) {
            api = "gpu_util" // 内存和设备计算的使用率
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              self.usagerateData.rows[len - 1]['GPU ' + i.toString()] = Number((Number(response.data['gpu_util']) / 100).toFixed(2))
              // var pieJson = {id:i,pieData:{columns: ['type', 'value'],rows: [{ type: '占比', value: 0 }]}}

              self.memData[i].pieData.rows[0].value = (response.data['mem_util'] / 100).toFixed(2)
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_fan"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              self.fanData.rows[len - 1]['GPU ' + i.toString()] = Number((Number(response.data['fan']) / 100).toFixed(2))
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_temp"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              self.tempData.rows[len - 1]['GPU ' + i.toString()] = response.data['cur_temp']
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_power"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              self.powerData.rows[len - 1]['GPU ' + i.toString()] = response.data['power_usage']
            })
            .catch(function (error) {
              console.log(error)
            })

            api = "gpu_perfstate"
            await axios.post(queryURL+api,{ "gpu_index":i
            }).then(function (response) {
              self.tableData[i]["工作状态"] = response.data['power_state']
            })
            .catch(function (error) {
              console.log(error)
            })
        }
      }catch(err){
        console.log(err)
      }
        // console.log(this.tempData.rows)

        // console.log(axisData);
      },
      // 这是一个定时器
      timer() {
          return setInterval(()=>{
              this.getData()
      },this.intervalTime)
    }
  },
  mounted() {
      this.getStaticInfo()
      // console.log("加载完成")
      // this.getData()
  },
  created() {
      // console.log("创建完成")
      // this.getData()
  },
  activated(){
      this.timer_id = this.timer()

      // console.log("重新载入")
  },
  deactivated() {
      // console.log("缓存起来")
      clearInterval(this.timer_id)
      this.timer_id = false

  },
  beforeDestroy() {
      // console.log("销毁")
      clearInterval(this.timer_id)
      this.timer_id = false

  }
}
</script>
<style>
</style>
