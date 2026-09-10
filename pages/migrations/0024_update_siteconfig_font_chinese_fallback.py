"""
v1.1.14: 把 SiteConfig 已存在的字体默认值更新为含中文 fallback 的版本。

背景：
  - Django 模板 `{{ config.font_family_body }}` 默认 HTML 转义，把 ' 转成 &#x27;
  - 旧默认 `'Inter', 'Helvetica Neue', Arial, sans-serif` 没有中文 fallback
  - iOS 自动 fallback 到 SF Pro + PingFang SC，baseline 不对齐 → 中英文混排参差
  - 安卓 fallback 到 Roboto + Noto Sans CJK，保持中英文字宽统一 → 看起来更整齐
  - 用户报告"安卓系统看到的字体更好一点"的真正根因是字体栈缺中文 fallback

修复：
  - 模型层默认值已更新（含 PingFang SC / Noto Sans CJK）
  - 本 migration 把已存在的 SiteConfig 单例记录也更新到新值
  - 若管理员手动改过字体（与默认不同），保留管理员的设置不动
"""
from django.db import migrations


OLD_DEFAULTS = (
    "'Inter', 'Helvetica Neue', Arial, sans-serif",
    "Inter, 'Helvetica Neue', Arial, sans-serif",
    "'Inter', 'Helvetica Neue', Arial",
    "Inter, Helvetica Neue, Arial, sans-serif",
)

NEW_DEFAULT_BODY = (
    "'Inter', -apple-system, BlinkMacSystemFont, system-ui, "
    "'PingFang SC', 'Hiragino Sans GB', "
    "'Microsoft YaHei', 'Source Han Sans CN', 'Noto Sans CJK SC', "
    "Roboto, sans-serif"
)
NEW_DEFAULT_HEADING = NEW_DEFAULT_BODY  # 同样升级


def update_defaults(apps, schema_editor):
    SiteConfig = apps.get_model('pages', 'SiteConfig')
    for cfg in SiteConfig.objects.all():
        # 仅当当前值与"老默认值"之一匹配时才升级 —— 保护管理员的自定义
        body_changed = cfg.font_family_body in OLD_DEFAULTS
        head_changed = cfg.font_family_heading in OLD_DEFAULTS
        if body_changed:
            cfg.font_family_body = NEW_DEFAULT_BODY
        if head_changed:
            cfg.font_family_heading = NEW_DEFAULT_HEADING
        if body_changed or head_changed:
            cfg.save(update_fields=[
                'font_family_body', 'font_family_heading'])


def revert_defaults(apps, schema_editor):
    """回滚：恢复到任一老默认值（精确恢复不可行，这里仅删中文 fallback）"""
    SiteConfig = apps.get_model('pages', 'SiteConfig')
    legacy = "'Inter', 'Helvetica Neue', Arial, sans-serif"
    for cfg in SiteConfig.objects.all():
        if 'PingFang SC' in (cfg.font_family_body or ''):
            cfg.font_family_body = legacy
        if 'PingFang SC' in (cfg.font_family_heading or ''):
            cfg.font_family_heading = legacy
        if 'PingFang SC' in (cfg.font_family_body or '') or \
           'PingFang SC' in (cfg.font_family_heading or ''):
            cfg.save(update_fields=[
                'font_family_body', 'font_family_heading'])


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0023_alter_visitor_ip_address'),
    ]
    operations = [
        migrations.RunPython(update_defaults, revert_defaults),
    ]
