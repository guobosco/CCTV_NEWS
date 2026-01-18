// pages/detail/detail.js
// 新闻详情页面，用于显示单条新闻的详细内容

// 创建页面实例
Page({
  /**
   * 页面的初始数据
   * 用于存储页面的状态和数据
   */
  data: {
    loading: true, // 加载状态标识，true表示正在加载，false表示加载完成
    news: { // 新闻详情对象
      id: '', // 新闻ID，唯一标识符
      title: '', // 新闻标题
      date: '', // 新闻日期
      content: '' // 新闻内容
    }
  },

  /**
   * 生命周期函数--监听页面加载
   * 当页面加载时触发，用于初始化页面数据
   * @param {Object} options - 页面跳转时传递的参数对象
   */
  onLoad: function(options) {
    // 从options中解构获取参数，options是页面跳转时传递的数据
    // 使用 || '' 设置默认值，防止参数不存在时出错
    var id = options.id || ''; // 新闻ID
    var title = options.title || ''; // 新闻标题
    var date = options.date || ''; // 新闻日期
    
    // 设置初始数据到页面数据对象中
    // 使用this.setData()方法更新数据，会触发页面重新渲染
    this.setData({
      'news.id': id, // 更新news对象的id属性
      'news.title': title, // 更新news对象的title属性
      'news.date': date // 更新news对象的date属性
    });
    
    // 调用获取新闻详情的方法，传入新闻ID
    this.getNewsDetail(id);
  },

  /**
   * 获取新闻详情数据
   * 异步方法，用于从后端API获取新闻详情
   * @param {string} id - 新闻ID
   */
  getNewsDetail: function(id) {
    // 保存this上下文，在异步回调中使用
    // 因为在Promise的回调函数中，this的指向会改变
    var that = this;
    
    // 设置加载状态为true，显示加载提示
    that.setData({
      loading: true
    });
    
    // 调用请求新闻详情的方法，返回Promise对象
    that.requestNewsDetail(id)
      // Promise成功回调，获取到新闻详情数据
      .then(function(newsDetail) {
        // 更新页面数据，显示新闻详情
        that.setData({
          'news.title': newsDetail.title, // 更新新闻标题
          'news.content': newsDetail.content, // 更新新闻内容
          loading: false // 设置加载状态为false，隐藏加载提示
        });
        
        // 在控制台打印成功日志，便于调试
        console.log('获取新闻详情成功:', newsDetail);
      })
      // Promise失败回调，处理请求失败情况
      .catch(function(error) {
        // 在控制台打印错误日志
        console.error('获取新闻详情失败:', error);
        // 失败时清空新闻内容，隐藏加载提示
        that.setData({
          'news.content': '', // 清空新闻内容
          loading: false // 隐藏加载提示
        });
      });
  },

  /**
   * 请求新闻详情API
   * 封装wx.request网络请求，返回Promise对象
   * @param {string} id - 新闻ID
   * @returns {Promise} - 返回Promise对象，用于处理异步请求结果
   */
  requestNewsDetail: function(id) {
    // 返回Promise对象，便于链式调用
    return new Promise(function(resolve, reject) {
      // 调用微信小程序的网络请求API
      wx.request({
        url: 'http://localhost:5001/db/news_detail?id=' + id, // API请求地址，拼接新闻ID
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
          // 检查响应状态码，200表示请求成功
          if (response.statusCode === 200) {
            // 检查返回的数据结构是否正确
            if (response.data.code === 200 && response.data.data) {
              // 请求成功，调用resolve返回数据
              resolve(response.data.data);
              return; // 结束函数执行
            }
          }
          // 请求失败或数据结构不正确，返回默认空对象
          resolve({ title: '', content: '' });
        },
        
        /**
         * 请求失败回调函数
         * 网络请求失败时触发
         */
        fail: function() {
          // 网络请求失败，返回默认空对象
          resolve({ title: '', content: '' });
        }
      });
    });
  }
});