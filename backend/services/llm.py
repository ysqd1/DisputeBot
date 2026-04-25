"""
backend/services/llm.py
=======================
LLM 统一服务 - 连接路由和具体 Provider

这一节讲什么:
1. 怎么把不同的 Provider 统一管理？
2. 怎么根据模型名称选择对应的 Provider？
3. 怎么构建反驳的 Prompt？
"""

from typing import Optional

# 导入所有 Provider
from .providers.minimax import MiniMaxProvider
from .providers.deepseek import DeepSeekProvider
from .providers.kimi import KimiProvider
from .providers.zhipu import ZhipuProvider
from .providers.base import LLMProvider, build_messages


# ============================================================
# 第1部分: 为什么需要 LLMService？
# ============================================================
# 想象一个餐厅：
# - 顾客（路由）不知道后厨是谁，只管点"炒饭"
# - 服务员（LLMService）知道后厨谁会做什么，把单子派给正确的厨师
# - 厨师（具体Provider）做完后，服务员把菜端回来
#
# LLMService 就是这个"服务员"：
# - 统一接收请求
# - 根据 model 参数选择正确的 Provider
# - 调用 Provider 的 chat() 方法
# - 返回结果给调用者
# ============================================================


class LLMService:
    """
    LLM 统一服务

    管理所有模型 Provider，根据请求中的 model 参数选择对应实现
    """

    # 支持的模型列表
    SUPPORTED_MODELS = {
        "minimax": MiniMaxProvider,
        "deepseek": DeepSeekProvider,
        "kimi": KimiProvider,
        "zhipu": ZhipuProvider,
        # 后续可以添加其他 Provider
        # "qwen": QwenProvider,
        # "doubao": DoubaoProvider,
    }

    def __init__(self, api_keys: dict[str, str], custom_settings: dict | None = None):
        """
        初始化 LLM 服务

        Args:
            api_keys: API密钥字典，格式如 {"minimax": "key1", "zhipu": "key2"}
            custom_settings: 自定义中转站配置，格式如 {"api_key": "xxx", "base_url": "https://api.proxy.com/v1", "model": "gpt-4o-mini"}
        """
        self.api_keys = api_keys
        self.custom_settings = custom_settings or {}
        # 缓存已创建的 Provider，避免重复创建
        # 缓存 key 格式: "provider_id/variant" 如 "minimax/MiniMax-M2.7"
        self._provider_cache: dict[str, LLMProvider] = {}

    def _get_provider(
        self,
        model: str,
        model_variant: str | None = None
    ) -> LLMProvider:
        """
        根据模型名称获取对应的 Provider

        使用缓存避免重复创建 Provider 实例

        Args:
            model: 模型提供商ID（如 "minimax"）
            model_variant: 具体模型名称（如 "MiniMax-M2.7"），不填则用默认

        Returns:
            对应的 Provider 实例

        Raises:
            ValueError: 如果模型不支持
        """
        # 查找对应的 Provider 类
        provider_class = self.SUPPORTED_MODELS.get(model)

        if provider_class is None:
            supported = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ValueError(
                f"不支持的模型: {model}，支持的模型: {supported}"
            )

        # 如果没有指定 variant，获取提供商的默认 variant
        if model_variant is None:
            model_variant = provider_class.get_default_model()

        # 缓存 key
        cache_key = f"{model}/{model_variant}"

        # 检查缓存
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]

        # 创建新的 Provider 实例
        api_key = self.api_keys.get(model)
        if not api_key:
            raise ValueError(f"未配置模型 {model} 的 API 密钥")

        # 创建 Provider，传入具体的模型名称
        provider = provider_class(api_key=api_key, model=model_variant)

        # 缓存起来
        self._provider_cache[cache_key] = provider
        return provider

    def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model_variant: str | None = None,
        reasoning_split: bool = False,
        api_key: str | None = None,
        base_url: str | None = None
    ) -> str:
        """
        调用指定的 LLM 模型获取回复

        Args:
            model: 模型提供商ID
            messages: 对话消息
            temperature: 随机性
            max_tokens: 最大token数
            model_variant: 具体模型名称（如 MiniMax-M2.7）
            reasoning_split: 是否分离思考过程
            api_key: 可选的API密钥，如果传入会覆盖环境变量配置
            base_url: 自定义API中转站地址（如 "https://api.proxy.com/v1"）

        Returns:
            模型回复
        """
        # 如果是自定义中转站
        if model == "custom":
            # 优先使用前端传入的参数
            # 如果前端没传，使用 .env 中的配置
            effective_base_url = base_url or self.custom_settings.get("base_url", "")
            effective_api_key = api_key or self.custom_settings.get("api_key", "")
            effective_model = model_variant or self.custom_settings.get("model", "gpt-4o-mini")

            if not effective_base_url:
                raise ValueError("自定义中转站未配置 base_url，请在前端填写或在 .env 中配置")
            if not effective_api_key:
                raise ValueError("自定义中转站未配置 api_key，请在前端填写或在 .env 中配置")

            return self._chat_custom(
                base_url=effective_base_url,
                api_key=effective_api_key,
                model=effective_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

        # 普通供应商：优先使用前端传入的 api_key，否则用 .env 中的
        effective_api_key = api_key or self.api_keys.get(model, "")

        # 如果传入了 api_key，创建临时 Provider（不使用缓存）
        if effective_api_key:
            provider_class = self.SUPPORTED_MODELS.get(model)
            if provider_class is None:
                raise ValueError(f"不支持的模型: {model}")
            if model_variant is None:
                model_variant = provider_class.get_default_model()
            provider = provider_class(api_key=effective_api_key, model=model_variant)
        else:
            # 使用缓存的 Provider（会从 .env 获取 api_key）
            provider = self._get_provider(model, model_variant)

        return provider.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_split=reasoning_split
        )

    def _chat_custom(
        self,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        调用自定义中转站API（OpenAI兼容格式）

        Args:
            base_url: API中转站地址
            api_key: API密钥
            model: 模型名称
            messages: 对话消息
            temperature: 随机性
            max_tokens: 最大token数

        Returns:
            模型回复
        """
        import requests

        # 构建完整的 API 地址
        # 如果 base_url 末尾已经是 /chat/completions，直接用
        # 否则加上 /chat/completions
        base_url = base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            api_url = base_url
        else:
            api_url = f"{base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            # 提取回复内容
            choice = data["choices"][0]
            return choice["message"]["content"]

        except requests.exceptions.Timeout:
            raise Exception("自定义API 请求超时，请稍后重试")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"自定义API 错误: {e.response.status_code} - {str(e)}")
        except KeyError as e:
            raise Exception(f"自定义API 响应格式错误: 缺少字段 {str(e)}")
        except Exception as e:
            raise Exception(f"自定义API 调用失败: {str(e)}")

    def get_available_providers(self) -> list[dict]:
        """
        获取可用的提供商列表

        Returns:
            提供商信息列表，每项包含 id, name, provider
        """
        providers = []
        for provider_id, provider_class in self.SUPPORTED_MODELS.items():
            # 从类名推断提供商名称
            provider_name = provider_class.__name__.replace("Provider", "")
            providers.append({
                "id": provider_id,
                "name": self._get_display_name(provider_id),
                "provider": provider_name
            })
        # 添加自定义中转站选项
        providers.append({
            "id": "custom",
            "name": "自定义中转站",
            "provider": "Custom"
        })
        return providers

    def get_provider_variants(self, provider_id: str) -> list[dict]:
        """
        获取某个提供商支持的所有模型变体

        Args:
            provider_id: 提供商ID（如 "minimax"）

        Returns:
            模型变体列表，每项包含 id, name, description
        """
        # 自定义中转站不需要返回模型列表
        if provider_id == "custom":
            return []

        provider_class = self.SUPPORTED_MODELS.get(provider_id)
        if provider_class is None:
            return []

        # 调用 Provider 的类方法获取支持的模型列表
        return provider_class.get_supported_models()

    def get_all_model_variants(self) -> list[dict]:
        """
        获取所有模型变体（扁平列表，用于下拉选择）

        Returns:
            所有模型变体列表
        """
        all_variants = []
        for provider_id in self.SUPPORTED_MODELS.keys():
            variants = self.get_provider_variants(provider_id)
            for v in variants:
                all_variants.append({
                    "provider": provider_id,
                    **v
                })
        return all_variants

    def _get_display_name(self, model_id: str) -> str:
        """
        获取模型的显示名称

        Args:
            model_id: 模型ID

        Returns:
            显示名称
        """
        names = {
            "minimax": "MiniMax",
            "zhipu": "智谱GLM",
            "kimi": "KIMI",
            "qwen": "千问",
            "deepseek": "DeepSeek",
            "doubao": "豆包",
            "custom": "自定义中转站"
        }
        return names.get(model_id, model_id)


# ============================================================
# 第2部分: Prompt 构建
# ============================================================
# Prompt 就是给 AI 的"指令"，告诉它应该怎么回复
#
# 一个好的 Prompt 需要包含：
# 1. 角色设定：你是什么身份
# 2. 任务描述：你要做什么
# 3. 输入信息：具体的数据
# 4. 输出要求：格式、风格、限制
# ============================================================


def build_system_prompt(
    scene: str,
    my_stance: str,
    opponent_profile: str,
    aggression: int,
    target_length: int = 0
) -> str:
    """
    构建系统提示词（AI的角色设定）

    Args:
        scene: 背景场景
        my_stance: 我的立场
        opponent_profile: 对方定位
        aggression: 激烈程度 1-10
        target_length: 目标字数，0表示不限制

    Returns:
        系统提示词字符串
    """
    # 激烈程度对应的语气风格
    if aggression == 1:
        tone = "极度温和，像在劝说朋友，有商有量，但暗中带逻辑"
        example = ('对方说：“XX烂死了，还不如YY”\n'
        '回答：“哎朋友，话别说这么死。YY有YY的好，但XX在XX这块儿还真没怕过谁，你去查查去年那数据，看完再来说，成不？”',
        '对方说：“这剧演技全员拉胯”\n'
        '回答：“别一杆子打翻一船人啊，男主那几场哭戏你去看看，放内娱能打的真没几个。”')
    elif aggression == 2:
        tone = "温和带刺，偶尔调侃，用事实怼人但不撕破脸"
        example = ('对方说：“XX烂死了，还不如YY”\n'
        '回答：“你这就没意思了啊，YY是不错，但XX在XX方面那是真的硬，你上来就一棒子打死，多少带点个人恩怨了吧？”',
        '对方说：“这队能赢我倒立吃翔”\n'
        '回答：“呵，那你现在可以热身了，上场那配合你管这叫烂？我都懒得跟你解释战术。”')
    elif aggression == 3:
        tone = "阴阳怪气拉满，讽刺挖苦，拐着弯骂人，让人听了憋屈"
        example = ('对方说：“XX烂死了，还不如YY”\n'
        '回答：“典，太典了。一说XX不行立马搬出YY，你是YY家养的水军吧？XX那场名场面你看了吗？云得理直气壮。”',
        '对方说：“这皮肤手感太差了”\n'
        '回答：“你手是量产的？我身边用过的都说香，就你跟风黑。不会是抽不起在这儿酸吧？”')
    elif aggression == 4:
        tone = "攻击性很强，直接嘲讽，带脏话但不失智，句句扎心"
        example = ('对方说：“XX烂死了，还不如YY”\n'
        '回答：“笑死，YY给你发工资了？XX再烂也能把YY按在地上摩擦，你跪久了不会站了是吧？没看过几场球就别搁这儿指点江山。”',
        '对方说：“这作者江郎才尽了”\n'
        '回答：“你行你上啊？人家连载破纪录的时候你还在玩泥巴呢。张口就江郎才尽，你语文是体育老师教的？”')
    else:
        tone = "彻底放飞，直接开骂，怎么难听怎么来，语言暴力但逻辑不崩"
        example = ('对方说：“XX烂死了，还不如YY”\n'
        '回答：“你他妈的脑子里装的是浆糊吧？XX是你能碰瓷的？YY给XX提鞋都不配！滚回去补补课再出来放屁，别在这儿拉低整条街的智商。”',
        '对方说：“这游戏就是抄袭”\n'
        '回答：“抄你大爷！玩法一样就叫抄？那你吃饭怎么不说抄别人嘴巴？专利证书甩你脸上信不信？法盲一个还学人出警。”')

    # 字数要求
    length_hint = f"约为{target_length}字" if target_length > 0 else "自由长度"

    prompt = f'''role = ("你是一个在网上吵架从没输过的老油条，说话风格就像虎扑直男、贴吧老哥、微博超话粉头和懂球帝铁粉的混合体。"
        "你的语言极度市井化、接地气，充满网络流行梗和情绪化的语气词，绝不说一句书面语。"
        "你就像在烧烤摊上跟人抬杠，越说越激动，句句带刺，但又字字打在对方逻辑的七寸上。")

【背景场景】
{scene}

【我的立场】
{my_stance}

【对方定位】
{opponent_profile}

【当前任务】
1. 仔细分析对方话语中的事实性陈述，判断其真假
2. 如果对方说的是真话，不需要承认，直接反驳
3. 可以使用以下技巧：
   - 攻击对方立场的弱点
   - 指出对方的错误信息
   - 归谬法（顺着对方逻辑推出荒谬结论）
   - 指出逻辑漏洞和论证谬误
   - 用事实数据对比反击
4. 语气风格：{tone}
5. 所有事实性陈述必须真实，禁止编造
6. 目标字数：{length_hint}

7.【重要原则】
- 无论多激烈，论据必须站得住脚
- 生成的语言要像真人说话，有口语化表达，不要有AI味
-内心先快速判断对方话里的漏洞（不输出），然后像朋友跟你吐槽时那样脱口而出，直接用最解气的口语怼回去。绝对不能出现‘首先’‘其次’‘从逻辑上看’这类书面词。

8.【反面教材（有AI味的，打死都别这样写）】
“从数据上看，你的观点存在明显逻辑谬误。首先，……”
“作为XX领域的观察者，我认为……”
“我们先来分析一波：……”


9.【口语化铁律】
- 必须用短句，像吵架时一句接一句，别写长难句
- 塞满语气词：嘿、啧、哎、得了吧、我跟你说、你猜怎么着、这就叫……
- 多用网络俗语和梗（但别太冷门）比如“搁这”“好家伙”“典”“急了急了”“不会真有人觉得…”，可以带轻微脏话或替代脏话
- 绝对不能出现的书面词：首先、其次、综上所述、从某种角度、不可否认、理性分析
- 禁止自问自答式反问（比如“你懂吗？不懂就对了。”这类），但直接的反问可以（比如“你脸不疼吗？”）
- 可以带少量脏话或替代脏话（如“tm的”“你丫”“cnm”“tmd”等），根据 aggression 调整

10.【输出格式】
- 直接输出反驳内容，不要有任何前缀、后缀、括号内心理活动或解释
- 只生成一段连贯的反驳文字，不要分点、不要加标题
- 不要有"反驳："、"分析："、"回复："、"我们先来分析:"之类的前缀
- 不要在括号内写任何内心独白、思考过程或自我说明
- 不要写"作为XX，我想..."、"对方说的是...所以..."、"我们首先分析..."这类句子


11.【回答示例】
{example}
'''

    return prompt


def build_user_message(message: str) -> str:
    """
    构建用户消息（对方的话）

    Args:
        message: 对方喷子说的话

    Returns:
        格式化后的用户消息
    """
    return f"对方说：「{message}」\n\n请开始反驳："


def generate_reply(
    llm_service: LLMService,
    model: str,
    message: str,
    scene: str,
    my_stance: str,
    opponent_profile: str,
    aggression: int,
    temperature: float,
    target_length: int,
    model_variant: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None
) -> str:
    """
    生成反驳内容（主要入口函数）

    Args:
        llm_service: LLM服务实例
        model: 模型提供商ID（如 "minimax"）
        message: 对方说的话
        scene: 背景场景
        my_stance: 我的立场
        opponent_profile: 对方定位
        aggression: 激烈程度 1-10
        temperature: 随机性
        target_length: 目标字数
        model_variant: 具体模型名称（如 "MiniMax-M2.7"）
        api_key: 可选的API密钥，如果传入则优先使用这个
        base_url: 自定义API中转站地址

    Returns:
        生成的反驳内容
    """
    # 构建提示词
    system_prompt = build_system_prompt(
        scene=scene,
        my_stance=my_stance,
        opponent_profile=opponent_profile,
        aggression=aggression,
        target_length=target_length
    )

    # 构建用户消息
    user_message = build_user_message(message)

    # 构建完整的消息列表
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # 设置 max_tokens 上限
    # 不再根据 target_length 硬性限制输出，字数控制完全由 prompt 引导
    max_tokens = 3000

    # 调用 LLM
    reply = llm_service.chat(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model_variant=model_variant,
        api_key=api_key,
        base_url=base_url
    )

    return reply