// pages/index/index.js
// 新闻列表页面，用于显示选定日期的新闻标题列表

// 创建页面实例
Page({
  /**
   * 页面的初始数据
   * 用于存储页面的状态和数据
   */
  data: {
    loading: true, // 加载状态标识，true表示正在加载，false表示加载完成
    currentDate: '', // 当前选择的日期，格式为YYYY-MM-DD
    today: '', // 今天的日期，格式为YYYY-MM-DD
    earliestDate: '2023-01-01', // 最早可以选择的日期，用于限制日期选择器范围
    newsItems: [] // 新闻标题列表数组，存储当前日期的新闻标题数据
  },

  /**
   * 生命周期函数--监听页面加载
   * 当页面加载时触发，用于初始化页面数据
   */
  onLoad: function() {
    // 获取当前时间，创建Date对象
    var now = new Date();
    
    // 格式化今天的日期，转换为YYYY-MM-DD格式
    // getFullYear() 获取年份
    // getMonth() 获取月份，返回值为0-11，需要+1
    // getDate() 获取日期
    // String().padStart(2, '0') 确保月份和日期为两位数
    var todayYear = now.getFullYear();
    var todayMonth = String(now.getMonth() + 1).padStart(2, '0');
    var todayDay = String(now.getDate()).padStart(2, '0');
    var todayStr = todayYear + '-' + todayMonth + '-' + todayDay;
    
    // 默认显示今天的新闻
    var defaultDate = todayStr;
    
    // 设置页面初始数据
    this.setData({
      today: todayStr, // 今天的日期
      currentDate: defaultDate // 默认显示的日期
    });
    
    // 调用获取新闻标题列表的方法，传入默认日期
    this.fetchNewsItems(defaultDate);
  },

  /**
   * 获取新闻标题列表数据
   * 异步方法，用于从后端API获取指定日期的新闻标题列表
   * @param {string} date - 新闻日期，格式为YYYY-MM-DD
   */
  fetchNewsItems: function(date) {
    // 保存this上下文，在异步回调中使用
    var that = this;
    
    // 设置加载状态为true，显示加载提示
    that.setData({
      loading: true
    });
    
    // 调用请求新闻标题列表的方法，返回Promise对象
    that.requestNewsItems(date)
      // Promise成功回调，获取到新闻标题列表数据
      .then(function(newsItems) {
        // 更新页面数据，显示新闻标题列表
        that.setData({
          newsItems: newsItems, // 更新新闻标题列表
          loading: false // 设置加载状态为false，隐藏加载提示
        });
        
        // 在控制台打印成功日志，便于调试
        console.log('获取新闻标题列表成功:', newsItems);
      })
      // Promise失败回调，处理请求失败情况
      .catch(function(error) {
        // 在控制台打印错误日志
        console.error('获取新闻标题列表失败:', error);
        // 失败时清空新闻标题列表，隐藏加载提示
        that.setData({
          newsItems: [], // 清空新闻标题列表
          loading: false // 隐藏加载提示
        });
      });
  },

  /**
   * 请求新闻标题列表API
   * 封装wx.request网络请求，返回Promise对象
   * @param {string} date - 新闻日期，格式为YYYY-MM-DD
   * @returns {Promise} - 返回Promise对象，用于处理异步请求结果
   */
  requestNewsItems: function(date) {
    // 返回Promise对象，便于链式调用
    return new Promise(function(resolve, reject) {
      // 调用微信小程序的网络请求API
      wx.request({
        url: 'http://localhost:5001/db/news_list?date=' + date, // API请求地址，拼接新闻日期
        method: 'GET', // 请求方法，GET用于获取数据
        header: { // 请求头，设置内容类型
          'content-type': 'application/json' // 表示请求的数据类型为JSON
        },
        timeout: 10000, // 请求超时时间，10秒
        
        /**
         * 请求成功回调函数
         * @param {Object} response - 响应对象，包含返回的数据
         */
        success: function(response) {
          // 打印后端返回的数据，便于调试
          console.log('后端返回数据:', response.data);
          
          // 检查响应状态码，200表示请求成功
          if (response.statusCode === 200) {
            // 检查返回的数据结构是否正确
            if (response.data.code === 200) {
              // 检查是否有items数组，确保数据格式正确
              if (response.data.data && response.data.data.items && Array.isArray(response.data.data.items)) {
                // 格式化返回的数据，转换为页面需要的格式
                var newsItems = response.data.data.items.map(function(item) {
                  // 解析新闻条目编号，item.item_number格式为"1/12"，只取前面的数字部分
                  var number = '';
                  if (item.item_number) {
                    number = item.item_number.split('/')[0];
                  }
                  
                  // 返回格式化后的新闻条目对象
                  return {
                    id: item.id, // 新闻ID
                    number: number, // 新闻条目编号
                    title: item.title, // 新闻标题
                    link: item.link // 新闻链接
                  };
                });
                // 请求成功，返回格式化后的新闻条目数组
                resolve(newsItems);
              } else {
                // items数组不存在或格式不正确，返回空数组
                resolve([]);
              }
              return;
            }
          }
          
          // 请求失败或数据结构不正确，返回空数组
          resolve([]);
        },
        
        /**
         * 请求失败回调函数
         * 网络请求失败时触发
         * @param {Object} error - 错误对象，包含错误信息
         */
        fail: function(error) {
          // 在控制台打印错误日志
          console.error('请求失败:', error);
          // 网络请求失败，返回空数组
          resolve([]);
        }
      });
    });
  },

  /**
   * 日期选择器变化事件处理函数
   * 当用户在日期选择器中选择日期时触发
   * @param {Object} e - 事件对象，包含用户选择的日期
   */
  onDateChange: function(e) {
    // 获取用户选择的日期，e.detail.value包含选择的日期
    var date = e.detail.value;
    
    // 更新当前选择的日期到页面数据
    this.setData({
      currentDate: date
    });
    
    // 调用获取新闻标题列表的方法，传入用户选择的日期
    this.fetchNewsItems(date);
  },

  /**
   * 跳转到新闻详情页
   * 当用户点击新闻标题时触发
   * @param {Object} e - 事件对象，包含新闻的ID、标题和日期
   */
  goToNewsDetail: function(e) {
    // 从事件对象中获取新闻的ID、标题和日期
    // e.currentTarget.dataset 包含通过data-*属性设置的数据
    var newsId = e.currentTarget.dataset.newsId || '';
    var newsTitle = e.currentTarget.dataset.newsTitle || '';
    var newsDate = e.currentTarget.dataset.newsDate || '';
    
    // 使用wx.navigateTo跳转到新闻详情页面
    // 拼接URL，传递新闻的ID、标题和日期作为参数
    wx.navigateTo({
      url: '/pages/detail/detail?id=' + newsId + '&title=' + encodeURIComponent(newsTitle) + '&date=' + newsDate
    });
  },

  /**
   * 格式化日期为YYYY-MM-DD格式
   * @param {Date} date - Date对象
   * @returns {string} - 格式化后的日期字符串，格式为YYYY-MM-DD
   */
  formatDate: function(date) {
    // 获取年份、月份和日期
    var year = date.getFullYear();
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var day = String(date.getDate()).padStart(2, '0');
    
    // 拼接为YYYY-MM-DD格式的字符串并返回
    return year + '-' + month + '-' + day;
  },

  /**
   * 切换到前一天
   * 当用户点击"前一天"按钮时触发
   */
  goToPrevDay: function() {
    // 创建当前日期的Date对象
    var currentDate = new Date(this.data.currentDate);
    
    // 设置日期为前一天
    currentDate.setDate(currentDate.getDate() - 1);
    
    // 格式化新日期为YYYY-MM-DD格式
    var newDate = this.formatDate(currentDate);
    
    // 检查新日期是否早于最早可以选择的日期
    if (newDate >= this.data.earliestDate) {
      // 更新当前选择的日期
      this.setData({
        currentDate: newDate
      });
      
      // 调用获取新闻标题列表的方法，传入新日期
      this.fetchNewsItems(newDate);
    }
  },

  /**
   * 切换到后一天
   * 当用户点击"后一天"按钮时触发
   */
  goToNextDay: function() {
    // 创建当前日期的Date对象
    var currentDate = new Date(this.data.currentDate);
    
    // 设置日期为后一天
    currentDate.setDate(currentDate.getDate() + 1);
    
    // 格式化新日期为YYYY-MM-DD格式
    var newDate = this.formatDate(currentDate);
    
    // 检查新日期是否晚于今天
    if (newDate <= this.data.today) {
      // 更新当前选择的日期
      this.setData({
        currentDate: newDate
      });
      
      // 调用获取新闻标题列表的方法，传入新日期
      this.fetchNewsItems(newDate);
    }
  }
});