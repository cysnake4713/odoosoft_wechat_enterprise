ODOO微信模块
===================================
提供Odoo和微信企业号间业务绑定。可能的使用场景有：
简单场景：
+ 同步odoo和微信企业号的用户，实现账户自动管理
+ 发送mail的地方可以同时自动发送微信通知
高级场景：
+ 使用odoo的触发器，自定义模板发送微信通知消息（jinja2模板）
+ 将微信消息回调和odoo结合，例如输入名称可以自动查相关的联系人信息

截图
----------------------------------
![概览](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/list.png)
![消息详情](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/detail.png)
![过滤器详情](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/filter.png)
![消息模板](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/message.png)


使用手册
---------------------------
####基本配置####
1. 在微信企业号中配置odoo调用组
![微信调用配置](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/wechat_server_config.png)
1. 配置公司参数
在 微信企业号 -> 设置 -> 账户 下， 会默认生成一个基本账户，可以直接配置此账户绑定到你申请的微信企业号，也可以新建一个新账户，此插件支持多企业号绑定，不同企业号之间用code字段向微信标示唯一性
![账户绑定](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/config_detail.png)
1. 配置应用
在微信企业号中配置一个应用,注意应用的ID
![账户绑定](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/wechat_server_app_config.png)
1. odoo端配置应用
在设置 —> 应用目录下配置 应用
![账户绑定](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/app_config.png)
1. 微信端设置回调
![账户绑定](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/app_callback.png)

####用户配置####


捐助
-----------------------------

![微信捐助](https://github.com/cysnake4713/odoosoft_wechat_enterprise/raw/master/static/img/wechat.png)
