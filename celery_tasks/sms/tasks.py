from libs.yuntongxun.sms import CCP
from celery_tasks.main import celery_app


@celery_app.task
def ccp_send_sms_code(mobile, sms_code):
    # 这里会返回发送状态　　０发送成功　　－１其他状态
    send_result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    print("当前验证码是:", sms_code)
    return send_result
