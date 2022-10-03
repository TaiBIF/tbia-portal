from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()

# TODO 這邊好像其實就是subtitle
partner_source_map = {
    'tesri': ['台灣生物多樣性網絡 TBN'],
    'brcas': ['臺灣生物多樣性資訊機構 TaiBIF','中央研究院生物多樣性中心植物標本資料庫'],
    'forest': ['生態調查資料庫系統'],
    'cpami': ['臺灣國家公園生物多樣性資料庫'],
    'tcd': ['濕地環境資料庫'], # 城鄉發展分署
    'oca': ['iOcean海洋保育網'],
    'tfri': ['林業試驗所植物標本資料庫'],
}