[app]
title = CyberLife
package.name = cyberlife
package.domain = org.zzy
source.dir = .
source.include_exts = py,png,jpg,ttf,json
version = 0.1
# 关键：必须包含这几个库
requirements = python3,kivy,lunar-python
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
# 权限：如果以后要存文件可能需要
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1