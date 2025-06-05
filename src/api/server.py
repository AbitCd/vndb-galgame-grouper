"""
API服务器，提供远程调用接口
"""
import os
import json
import asyncio  # 保留，因为在async函数中需要
import sys
from aiohttp import web

# 确保项目根目录在Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.models import UserInputs
from src.core.input_channels import ApiChannel

# 其余代码保持不变

# 异步主函数
async def run_process(data):
    """
    运行主处理函数
    """
    try:
        # 验证输入
        channel = ApiChannel(data)
        user_inputs = channel.collect_inputs()
        
        # 导入主函数
        from main import async_main
        
        # 运行主处理函数
        await async_main(user_inputs)
        
        return {"success": True, "message": "处理完成"}
    except Exception as e:
        import traceback
        return {
            "success": False, 
            "message": str(e),
            "traceback": traceback.format_exc()
        }

# API处理器
async def handle_process(request):
    """
    处理API请求
    """
    try:
        data = await request.json()
        result = await run_process(data)
        return web.json_response(result)
    except json.JSONDecodeError:
        return web.json_response({"success": False, "message": "无效的JSON格式"}, status=400)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)}, status=500)

# 获取可用标签
async def handle_get_fields(request):
    """
    获取可用的标签字段
    """
    # 这里需要导入相关函数
    from src.core.data_parser import extract_valid_fields, parse_vn_response
    from src.core.vndb_api import fetch_vn_info_batch
    
    try:
        # 获取查询参数
        keyword = request.query.get('keyword')
        if not keyword:
            return web.json_response({"success": False, "message": "缺少keyword参数"}, status=400)
        
        # 查询VNDB
        json_data_dict = await fetch_vn_info_batch([keyword])
        
        # 解析结果
        result_dict = {}
        for kw, json_data in json_data_dict.items():
            parsed_data = parse_vn_response(json_data)
            if parsed_data:
                result_dict[kw] = parsed_data
        
        # 提取字段
        fields = extract_valid_fields(result_dict)
        
        return web.json_response({
            "success": True, 
            "fields": fields
        })
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)}, status=500)

# 模型定义
async def handle_get_model(request):
    """
    获取输入模型定义
    """
    model_schema = UserInputs.schema()
    return web.json_response(model_schema)

# 创建应用
def create_app():
    """
    创建Web应用
    """
    app = web.Application()
    app.router.add_post('/api/process', handle_process)
    app.router.add_get('/api/fields', handle_get_fields)
    app.router.add_get('/api/model', handle_get_model)
    return app

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="API服务器")
    parser.add_argument('--host', default='127.0.0.1', help='服务器主机 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口 (默认: 8080)')
    args = parser.parse_args()
    app = create_app()
    web.run_app(app, host=args.host, port=args.port)
