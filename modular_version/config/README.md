# 用户配置文件说明

## 配置文件结构

系统使用两个JSONL配置文件来管理用户账号：

1. **admin_config.jsonl** - 管理员账号配置
2. **user_config.jsonl** - 普通用户账号配置

## 配置格式

每个配置文件使用JSONL格式（每行一个JSON对象），格式如下：

```jsonl
{"username": "用户名", "password": "密码"}
{"username": "用户名2", "password": "密码2"}
```

## 添加新用户

### 添加管理员账号

编辑 `admin_config.jsonl`，每行添加一个用户：

```jsonl
{"username": "admin", "password": "admin123"}
{"username": "admin2", "password": "admin456"}
```

### 添加普通用户账号

编辑 `user_config.jsonl`，每行添加一个用户：

```jsonl
{"username": "annotator1", "password": "annotator123"}
{"username": "annotator2", "password": "annotator123"}
{"username": "newuser", "password": "newpass123"}
```

## 字段说明

- **username**: 登录用户名（必填）
- **password**: 登录密码（必填，明文存储）

## 权限说明

- **管理员 (admin)**: 拥有所有权限
- **普通用户 (annotator)**: 标注权限

## 注意事项

1. 密码使用明文存储，适合内部使用
2. 修改配置文件后，需要重启程序才能生效
3. 确保每行都是有效的JSON格式，否则该行会被跳过
4. 空行会被自动忽略

