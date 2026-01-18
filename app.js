// app.js
// 微信小程序应用入口文件

// 创建小程序实例
App({
  /**
   * 生命周期函数--监听小程序初始化
   * 当小程序初始化完成时，会触发 onLaunch（全局只触发一次）
   */
  onLaunch() {
    // 展示本地存储能力，获取历史日志记录
    // wx.getStorageSync('logs') 从本地存储中读取logs数据
    // || [] 表示如果logs不存在，则使用空数组作为默认值
    const logs = wx.getStorageSync('logs') || [];
    
    // 将当前时间戳添加到日志数组的开头
    // Date.now() 获取当前时间的时间戳（毫秒）
    // logs.unshift() 将元素添加到数组开头
    logs.unshift(Date.now());
    
    // 将更新后的日志数组保存回本地存储
    // wx.setStorageSync(key, value) 将数据存储在本地缓存中
    wx.setStorageSync('logs', logs);
  },
  
  /**
   * 全局数据对象
   * 用于存储可以在整个小程序中共享的数据
   */
  globalData: {
    // 用户信息，初始值为null
    // 可以在各个页面中通过 getApp().globalData.userInfo 访问
    userInfo: null
  }
});