import time
from urllib.parse import parse_qs
from django.conf import settings
from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utils.alipay import AliPay


def aliPay():
    obj = AliPay(
        appid="2016092400581835",                              # 支付宝沙箱里面的APPID
        app_notify_url="http://127.0.0.1:8800/update_order/",  # 如果支付成功，支付宝会向这个地址发送POST请求（校验是否支付已经完成），此地址要能够在公网进行访问
        return_url="http://127.0.0.1:8800/result/",            # 如果支付成功，重定向回到你的网站的地址。
        alipay_public_key_path="keys/alipay_public_2048.txt",  # 支付宝公钥
        app_private_key_path="keys/app_private_2048.txt",      # 应用私钥
        debug=True,  # 默认False,True表示使用沙箱环境测试
    )

    # 优化:在settings里面的设置后使用
    # obj = AliPay(
    #     appid=settings.APPID,
    #     app_notify_url=settings.NOTIFY_URL,
    #     return_url=settings.RETURN_URL,
    #     alipay_public_key_path=settings.PUB_KEY_PATH,
    #     app_private_key_path=settings.PRI_KEY_PATH,
    #     debug=True,
    # )
    return obj


@csrf_exempt
def index(request):
    if request.method == "GET":
        return render(request, 'index.html')

    # 实例化SDK里面的类AliPay
    alipay = aliPay()

    # 对购买的数据进行加密
    money = float(request.POST.get('price'))  # 保留俩位小数
    out_trade_no = "x2" + str(time.time())  # 商户订单号
    # 1. 在数据库创建一条数据：状态（待支付）

    query_params = alipay.direct_pay(
        subject="充气式Saber",  # 商品简单描述
        out_trade_no=out_trade_no,  # 商户订单号
        total_amount=money,  # 交易金额(单位: 元 保留俩位小数)
    )
    # 拼接url，转到支付宝支付页面
    pay_url = "https://openapi.alipaydev.com/gateway.do?{}".format(query_params)

    return redirect(pay_url)


@csrf_exempt
def update_order(request):
    """
    支付成功后，支付宝向该地址发送的POST请求（用于修改订单状态）
    :param request:
    :return:
    """
    if request.method == 'POST':
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)

        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        alipay = aliPay()

        sign = post_dict.pop('sign', None)
        status = alipay.verify(post_dict, sign)
        if status:
            # 1.修改订单状态
            out_trade_no = post_dict.get('out_trade_no')
            print(out_trade_no)
            # 2. 根据订单号将数据库中的数据进行更新

            return HttpResponse('支付成功')
        else:
            return HttpResponse('支付失败')
    return HttpResponse('')


def pay_result(request):
    """
    支付完成后，跳转回的地址
    :param request:
    :return:
    """
    params = request.GET.dict()
    sign = params.pop('sign', None)

    alipay = aliPay()

    status = alipay.verify(params, sign)

    if status:
        return HttpResponse('支付成功')
    return HttpResponse('支付失败')
