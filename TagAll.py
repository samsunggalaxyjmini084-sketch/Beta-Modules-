# meta developer: @yourhandle
# meta name: TagAll
# meta version: 2.0.41
#
# 01101110 01100101 01110110 01100101 01110010 00100000 01100111 01101001 01110110 01100101 00100000 01110101 01110000
# 01101110 01100101 01110110 01100101 01110010 00100000 01101100 01100101 01110100 00100000 01111001 01101111 01110101 00100000 01100100 01101111 01110111 01101110
# 01101110 01100101 01110110 01100101 01110010 00100000 01110010 01110101 01101110 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01100100 01100101 01110011 01100101 01110010 01110100 00100000 01111001 01101111 01110101
# 01101110 01100101 01110110 01100101 01110010 00100000 01101101 01100001 01101011 01100101 00100000 01111001 01101111 01110101 00100000 01100011 01110010 01111001 00100000 01101110 01100101 01110110 01100101 01110010 00100000 01110011 01100001 01111001 00100000 01100111 01101111 01101111 01100100 01100010 01111001 01100101
# 01101110 01100101 01110110 01100101 01110010 00100000 01110100 01100101 01101100 00100000 01100001 01101100 01101100 00100000 01100001 00100000 01101100 01101001 01100101 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 00100000 01101000 01110101 01110010 01110100 01111001 01101111 01110101
# (Rick Astley - Never Gonna Give You Up)

import asyncio
import contextlib
import logging
import random
import time
import re

from hikkatl.tl.functions.channels import InviteToChannelRequest
from hikkatl.tl.types import Message
from hikkatl import events # Required for message watcher

from .. import loader, utils

logger = logging.getLogger(__name__)


class StopEvent:
    """
    Event class to signal stopping the TagAll process.
    Stores the chat_id to ensure the trigger message comes from the correct chat.
    """

    def __init__(self, chat_id: int):
        self.state = True
        self.chat_id = chat_id
        self.last_timeout: float | None = None

    def stop(self):
        self.state = False


@loader.tds
class TagAllMod(loader.Module):
    """Отмечает всех участников чата, используя инлайн бот или классическим методом"""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат или тип чата не поддерживается для приглашения бота.</b>",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": (
            "Время между сообщениями с тегами. Можно указать одно значение (например, '0.1'),"
            " несколько значений через запятую (например, '0.1, 0.5, 1.0') или диапазон"
            " (например, '0.1-1.0')."
        ),
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя кнопку в сообщении"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Сколько пользователей тегать в одном сообщении",
        "_cfg_doc_duration": "Как долго (в секундах) должен работать процесс TagAll. Установите 0 для неограниченного времени.",
        "_cfg_doc_exclude_user_ids": "ID пользователя(ей), которых не нужно тегать. Разделяйте запятыми. Например: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "ID чата(ов), в которых разрешено использовать команды модуля TagAll. Разделяйте запятыми. Если указан только один ID, команды, запущенные в других чатах, будут автоматически перенаправлены в этот чат. Если пусто, команды разрешены во всех чатах.",
        "_cmd_tagall_doc": "[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        "_cmd_stoptagall_doc": "[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>.",
        "tagall_not_running": "🚫 <b>TagAll в данный момент не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}. Используйте <code>.stoptagall</code>, чтобы остановить его.</b>",
        "no_eligible_participants": "🚫 <b>В этом чате нет подходящих участников для тега.</b>",
        "cmd_redirected": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code>, так как он единственный разрешенный.",
        "cmd_not_allowed": "🚫 <b>Эта команда не может быть использована в текущем чате, и нет единственного разрешенного чата для перенаправления.</b>",
        "cmd_not_allowed_current": "🚫 <b>Эта команда не может быть использована в текущем чате.</b>",
        "cmd_redirected_indexed": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code> (индекс <code>{index}</code>).",
        "invalid_chat_index": "🚫 <b>Неверный индекс чата</b> <code>{index}</code>. Разрешенные чаты: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Эта команда не может быть использована в текущем чате. Укажите индекс чата или используйте в одном из разрешенных чатов:</b> {allowed_chats}.",
        # New trigger strings
        "_cfg_doc_trigger_system_enabled": "Включить или выключить систему триггеров.",
        "_cfg_doc_trigger_start_message": (
            "Сообщение-триггер для запуска TagAll. Если пусто, триггер не активен."
        ),
        "_cfg_doc_trigger_stop_message": (
            "Сообщение-триггер для остановки TagAll. Если пусто, триггер не активен."
        ),
        "_cfg_doc_trigger_chat_id": (
            "ID чата, в котором будут работать триггеры. Установите 0, чтобы триггеры"
            " работали в любом чате."
        ),
        "_cfg_doc_trigger_user_id": (
            "ID пользователя, который может активировать триггеры. Установите 0,"
            " чтобы любой пользователь мог активировать триггеры."
        ),
        "_cfg_doc_trigger_delete_message": (
            "Удалять ли сообщение-триггер после его срабатывания."
        ),
        "trigger_tagall_started": "✅ <b>TagAll запущен по триггеру в чате {chat_id}.</b>",
        "trigger_tagall_stopped": "✅ <b>TagAll остановлен по триггеру в чате {chat_id}.</b>",
        "trigger_tagall_already_running": "ℹ️ <b>TagAll уже запущен в чате {chat_id}, триггер проигнорирован.</b>",
        "trigger_tagall_not_running": "ℹ️ <b>TagAll не запущен в чате {chat_id}, триггер проигнорирован.</b>",
        "_cmd_autotagall_doc": "[on|off|true|false] - Включить/выключить систему триггеров. Без аргументов - переключить текущее состояние.",
        "triggers_enabled": "✅ <b>Система триггеров TagAll включена.</b>",
        "triggers_disabled": "❌ <b>Система триггеров TagAll выключена.</b>",
        "invalid_autotagall_arg": "🚫 <b>Неверный аргумент. Используйте 'on', 'off', 'true', 'false' или оставьте пустым.</b>",
    }

    strings_de = {
        "bot_error": "🚫 <b>Einladung des Inline-bots in den Chat fehlgeschlagen oder der Chat-Typ wird für Bot-Einladungen nicht unterstützt.</b>",
        "_cfg_doc_delete": "Nachrichten nach Erwähnung löschen",
        "_cfg_doc_use_bot": "Inline-Bot verwenden, um Leute zu erwähnen",
        "_cfg_doc_timeout": (
            "Zeitintervall, in dem zwischen den Erwähnungen gewartet wird. Kann ein"
            " einzelner Wert (z. B. '0.1'), mehrere durch Komma getrennte Werte (z. B."
            " '0.1, 0.5, 1.0') oder ein Bereich (z. B. '0.1-1.0') sein."
        ),
        "_cfg_doc_cycle_tagging": (
            "Alle Teilnehmer immer wieder erwähnen, bis du das Skript mit der"
            " Schaltfläche in der Nachricht stoppst"
        ),
        "_cfg_doc_cycle_delay": (
            "Verzögerung zwischen jedem Zyklus der Erwähnung in Sekunden"
        ),
        "_cfg_doc_chunk_size": "Wie viele Benutzer in einer Nachricht erwähnt werden sollen",
        "_cfg_doc_duration": "Wie lange (in Sekunden) der TagAll-Prozess laufen soll. Auf 0 für unbegrenzte Zeit einstellen.",
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht in Chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits in Chat {chat_id}. Verwenden Sie <code>.stoptagall</code>, um es zu stoppen.</b>",
        "_cfg_doc_exclude_user_ids": "Benutzer-ID(s), die nicht erwähnt werden sollen. Kommagetrennt eingeben. Zum Beispiel: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "Chat-ID(s), in denen die TagAll-Modulbefehle verwendet werden dürfen. Durch Kommas getrennt eingeben. Wenn nur eine ID angegeben ist, werden Befehle, die in anderen Chats ausgeführt werden, automatisch in diesen Chat umgeleitet. Wenn leer, sind Befehle in allen Chats erlaubt.",
        "_cmd_tagall_doc": "[<Chat-Nummer>] [Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet.",
        "_cmd_stoptagall_doc": "[<Chat-Nummer>] - Den laufenden TagAll-Prozess im <b>angegebenen oder aktuellen Chat</b> stoppen.",
        "no_eligible_participants": "🚫 <b>In diesem Chat gibt es keine geeigneten Teilnehmer zum Taggen.</b>",
        "cmd_redirected": "➡️ <b>Befehl wurde in Chat</b> <code>{target_chat_id}</code> umgeleitet, da dies der einzige erlaubte ist.",
        "cmd_not_allowed": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden, und es gibt keinen einzigen erlaubten Chat zur Umleitung.</b>",
        "cmd_not_allowed_current": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden.</b>",
        "cmd_redirected_indexed": "➡️ <b>Befehl wurde in Chat</b> <code>{target_chat_id}</code> (Index <code>{index}</code>) umgeleitet.",
        "invalid_chat_index": "🚫 <b>Ungültiger Chat-Index</b> <code>{index}</code>. Erlaubte Chats: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden. Geben Sie einen Chat-Index an oder verwenden Sie ihn in einem der erlaubten Chats:</b> {allowed_chats}.",
        # New trigger strings
        "_cfg_doc_trigger_system_enabled": "Triggersystem aktivieren oder deaktivieren.",
        "_cfg_doc_trigger_start_message": "Auslösernachricht zum Starten von TagAll. Leer lassen, um den Auslöser zu deaktivieren.",
        "_cfg_doc_trigger_stop_message": "Auslösernachricht zum Stoppen von TagAll. Leer lassen, um den Auslöser zu deaktivieren.",
        "_cfg_doc_trigger_chat_id": "Chat-ID, in der Auslöser funktionieren. Auf 0 setzen, damit Auslöser in jedem Chat funktionieren.",
        "_cfg_doc_trigger_user_id": "Benutzer-ID, die Auslöser aktivieren kann. Auf 0 setzen, damit jeder Benutzer Auslöser aktivieren kann.",
        "_cfg_doc_trigger_delete_message": "Auslösernachricht nach dem Auslösen löschen.",
        "trigger_tagall_started": "✅ <b>TagAll wurde durch einen Auslöser in Chat {chat_id} gestartet.</b>",
        "trigger_tagall_stopped": "✅ <b>TagAll wurde durch einen Auslöser in Chat {chat_id} gestoppt.</b>",
        "trigger_tagall_already_running": "ℹ️ <b>TagAll läuft bereits in Chat {chat_id}, Auslöser ignoriert.</b>",
        "trigger_tagall_not_running": "ℹ️ <b>TagAll läuft nicht in Chat {chat_id}, Auslöser ignoriert.</b>",
        "_cmd_autotagall_doc": "[on|off|true|false] - Triggersystem aktivieren/deaktivieren. Ohne Argumente - den aktuellen Status umschalten.",
        "triggers_enabled": "✅ <b>TagAll-Triggersystem aktiviert.</b>",
        "triggers_disabled": "❌ <b>TagAll-Triggersystem deaktiviert.</b>",
        "invalid_autotagall_arg": "🚫 <b>Ungültiges Argument. Verwenden Sie 'on', 'off', 'true', 'false' oder lassen Sie es leer.</b>",
    }

    strings_tr = {
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi veya sohbet türü bot davetleri için desteklenmiyor.</b>",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": (
            "Her etiket mesajı arasında ne kadar bekleneceği. Tek bir değer (örneğin,"
            " '0.1'), virgülle ayrılmış birden çok değer (örneğin, '0.1, 0.5, 1.0')"
            " veya bir aralık (örneğin, '0.1-1.0') belirtebilirsiniz."
        ),
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Bir mesajda kaç kullanıcı etiketlenecek",
        "_cfg_doc_duration": "TagAll sürecinin ne kadar süre (saniye) çalışması gerektiği. Sınırsız süre için 0 olarak ayarlayın.",
        "_cfg_doc_exclude_user_ids": "Etiketlenmeyecek kullanıcı kimliği(leri). Virgülle ayırın. Örneğin: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "TagAll modül komutlarının kullanılabileceği sohbet kimliği(leri). Virgülle ayırın. Yalnızca bir kimlik belirtilirse, diğer sohbetlerde başlatılan komutlar otomatik olarak bu sohbete yönlendirilecektir. Boş bırakılırsa, komutlara tüm sohbetlerde izin verilir.",
        "_cmd_tagall_doc": "[<Sohbet Numarası>] [metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir.",
        "_cmd_stoptagall_doc": "[<Sohbet Numarası>] - Çalışan TagAll sürecini <b>belirtilen veya mevcut sohbette</b> durdur.",
        "no_eligible_participants": "🚫 <b>Bu sohbette etiketlenecek uygun katılımcı yok.</b>",
        "cmd_redirected": "➡️ <b>Komut, izin verilen tek sohbet olduğu için</b> <code>{target_chat_id}</code> sohbetine yönlendirildi.",
        "cmd_not_allowed": "🚫 <b>Bu komut mevcut sohbette kullanılamaz ve yönlendirmek için tek bir izin verilen sohbet yok.</b>",
        "cmd_not_allowed_current": "🚫 <b>Bu komut mevcut sohbette kullanılamaz.</b>",
        "cmd_redirected_indexed": "➡️ <b>Komut,</b> <code>{target_chat_id}</code> (dizin <code>{index}</code>) sohbetine yönlendirildi.",
        "invalid_chat_index": "🚫 <b>Geçersiz sohbet dizini</b> <code>{index}</code>. İzin verilen sohbetler: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Bu komut mevcut sohbette kullanılamaz. Bir sohbet dizini belirtin veya izin verilen sohbetlerden birinde kullanın:</b> {allowed_chats}.",
        # New trigger strings
        "_cfg_doc_trigger_system_enabled": "Tetikleyici sistemini etkinleştir veya devre dışı bırak.",
        "_cfg_doc_trigger_start_message": "TagAll'u başlatmak için tetikleyici mesajı. Boş bırakılırsa tetikleyici etkin değildir.",
        "_cfg_doc_trigger_stop_message": "TagAll'u durdurmak için tetikleyici mesajı. Boş bırakılırsa tetikleyici etkin değildir.",
        "_cfg_doc_trigger_chat_id": "Tetikleyicilerin çalışacağı sohbet kimliği. Herhangi bir sohbette çalışması için 0 olarak ayarlayın.",
        "_cfg_doc_trigger_user_id": "Tetikleyicileri etkinleştirebilecek kullanıcı kimliği. Herhangi bir kullanıcının etkinleştirmesi için 0 olarak ayarlayın.",
        "_cfg_doc_trigger_delete_message": "Tetikleyici mesajı tetiklendikten sonra silinsin mi.",
        "trigger_tagall_started": "✅ <b>TagAll, {chat_id} sohbetinde tetikleyici ile başlatıldı.</b>",
        "trigger_tagall_stopped": "✅ <b>TagAll, {chat_id} sohbetinde tetikleyici ile durduruldu.</b>",
        "trigger_tagall_already_running": "ℹ️ <b>TagAll zaten {chat_id} sohbetinde çalışıyor, tetikleyici yoksayıldı.</b>",
        "trigger_tagall_not_running": "ℹ️ <b>TagAll {chat_id} sohbetinde çalışmıyor, tetikleyici yoksayıldı.</b>",
        "_cmd_autotagall_doc": "[on|off|true|false] - Tetikleyici sistemini etkinleştir/devre dışı bırak. Argüman yoksa - mevcut durumu değiştir.",
        "triggers_enabled": "✅ <b>TagAll tetikleyici sistemi etkinleştirildi.</b>",
        "triggers_disabled": "❌ <b>TagAll tetikleyici sistemi devre dışı bırakıldı.</b>",
        "invalid_autotagall_arg": "🚫 <b>Geçersiz argüman. 'on', 'off', 'true', 'false' kullanın veya boş bırakın.</b>",
    }

    strings_uz = {
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi yoki chat turi bot takliflari uchun qo‘llab-quvvatlanmaydi.</b>"
        ),
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": (
            "Har bir etiket xabari orasida nechta kutish kerak. Bitta qiymat (masalan,"
            " '0.1'), vergul bilan ajratilgan bir nechta qiymatlar (masalan,"
            " '0.1, 0.5, 1.0') yoki diapazon (masalan, '0.1-1.0') ko'rsatishingiz mumkin."
        ),
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi etiketlanadi",
        "_cfg_doc_duration": "TagAll jarayoni qancha vaqt (soniya) ishlashi kerak. Cheksiz vaqt uchun 0 ga o'rnating.",
        "_cfg_doc_exclude_user_ids": "Etiketlanmaydigan foydalanuvchi ID(lar)i. Vergul bilan ajrating. Misol uchun: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "TagAll modul buyruqlaridan foydalanishga ruxsat berilgan chat ID(lar)i. Vergul bilan ajrating. Agar faqat bitta ID ko'rsatilgan bo'lsa, boshqa chatlarda ishga tushirilgan buyruqlar avtomatik ravishda ushbu chatga yo'naltiriladi. Bo'sh bo'lsa, buyruqlarga barcha chatlarda ruxsat beriladi.",
        "_cmd_tagall_doc": "[<Chat raqami>] [matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilgan bo'lsa, teglar bilan birga yuboriladi. Matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi.",
        "_cmd_stoptagall_doc": "[<Chat raqami>] - Ishlayotgan TagAll jarayonini <b>ko'rsatilgan yoki joriy chatda</b> to'xtatish.",
        "no_eligible_participants": "🚫 <b>Bu chatda tegish uchun mos ishtirokchilar topilmadi.</b>",
        "cmd_redirected": "➡️ <b>Buyruq, ruxsat berilgan yagona chat bo'lgani uchun</b> <code>{target_chat_id}</code> chatiga yo'naltirildi.",
        "cmd_not_allowed": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi va yo'naltirish uchun yagona ruxsat berilgan chat yo'q.</b>",
        "cmd_not_allowed_current": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi.</b>",
        "cmd_redirected_indexed": "➡️ <b>Buyruq,</b> <code>{target_chat_id}</code> (indeks <code>{index}</code>) chatiga yo'naltirildi.",
        "invalid_chat_index": "🚫 <b>Noto'g'ri chat indeksi</b> <code>{index}</code>. Ruxsat berilgan chatlar: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi. Chat indeksini ko'rsating yoki ruxsat berilgan chatlardan birida foydalaning:</b> {allowed_chats}.",
        # New trigger strings
        "_cfg_doc_trigger_system_enabled": "Trigger tizimini yoqish yoki o'chirish.",
        "_cfg_doc_trigger_start_message": "TagAll'ni ishga tushirish uchun trigger xabari. Bo'sh qoldirilsa, trigger faol emas.",
        "_cfg_doc_trigger_stop_message": "TagAll'ni to'xtatish uchun trigger xabari. Bo'sh qoldirilsa, trigger faol emas.",
        "_cfg_doc_trigger_chat_id": "Triggerlar ishlaydigan chat ID. Triggerlar istalgan chatda ishlashi uchun 0 ga o'rnating.",
        "_cfg_doc_trigger_user_id": "Triggerlarni faollashtira oladigan foydalanuvchi ID. Har qanday foydalanuvchi faollashtirishi uchun 0 ga o'rnating.",
        "_cfg_doc_trigger_delete_message": "Trigger xabari ishga tushgandan so'ng o'chirilsinmi.",
        "trigger_tagall_started": "✅ <b>TagAll {chat_id} chatida trigger orqali ishga tushirildi.</b>",
        "trigger_tagall_stopped": "✅ <b>TagAll {chat_id} chatida trigger orqali to'xtatildi.</b>",
        "trigger_tagall_already_running": "ℹ️ <b>TagAll allaqachon {chat_id} chatida ishlamoqda, trigger e'tiborsiz qoldirildi.</b>",
        "trigger_tagall_not_running": "ℹ️ <b>TagAll {chat_id} chatida ishlamayapti, trigger e'tiborsiz qoldirildi.</b>",
        "_cmd_autotagall_doc": "[on|off|true|false] - Trigger tizimini yoqish/o'chirish. Argumentlar bo'lmasa - joriy holatni almashtirish.",
        "triggers_enabled": "✅ <b>TagAll trigger tizimi yoqildi.</b>",
        "triggers_disabled": "❌ <b>TagAll trigger tizimi o'chirildi.</b>",
        "invalid_autotagall_arg": "🚫 <b>Noto'g'ri argument. 'on', 'off', 'true', 'false' dan foydalaning yoki bo'sh qoldiring.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "delete",
                False,
                lambda: self.strings("_cfg_doc_delete"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "use_bot",
                False,
                lambda: self.strings("_cfg_doc_use_bot"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "timeout",
                "0.1",
                lambda: self.strings("_cfg_doc_timeout"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "cycle_tagging",
                False,
                lambda: self.strings("_cfg_doc_cycle_tagging"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "cycle_delay",
                0,
                lambda: self.strings("_cfg_doc_cycle_delay"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "chunk_size",
                3,
                lambda: self.strings("_cfg_doc_chunk_size"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "duration",
                0,
                lambda: self.strings("_cfg_doc_duration"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "exclude_user_ids",
                "",
                lambda: self.strings("_cfg_doc_exclude_user_ids"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "allowed_chat_ids",
                "",
                lambda: self.strings("_cfg_doc_allowed_chat_ids"),
                validator=loader.validators.String(),
            ),
            # New config for trigger system
            loader.ConfigValue(
                "trigger_system_enabled",
                True,
                lambda: self.strings("_cfg_doc_trigger_system_enabled"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "trigger_start_message",
                "",
                lambda: self.strings("_cfg_doc_trigger_start_message"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "trigger_stop_message",
                "",
                lambda: self.strings("_cfg_doc_trigger_stop_message"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "trigger_chat_id",
                0,  # 0 means any chat
                lambda: self.strings("_cfg_doc_trigger_chat_id"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "trigger_user_id",
                0,  # 0 means any user
                lambda: self.strings("_cfg_doc_trigger_user_id"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "trigger_delete_message",
                False,
                lambda: self.strings("_cfg_doc_trigger_delete_message"),
                validator=loader.validators.Boolean(),
            ),
        )
        self._tagall_events: dict[int, StopEvent] = {}
        self._message_watcher_handler = None # Re-introduce this

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        # Register the message watcher handler
        self._message_watcher_handler = self._client.add_event_handler(
            self._message_watcher, events.NewMessage()
        )

    async def on_unload(self):
        # Remove the message watcher handler
        if self._message_watcher_handler:
            self._client.remove_event_handler(self._message_watcher_handler)
            self._message_watcher_handler = None
            logger.info("Обработчик событий _message_watcher удален.")

        # Останавливаем все запущенные процессы TagAll
        # Итерируем по копии значений словаря, чтобы избежать RuntimeError, если словарь изменяется во время итерации
        for event in list(self._tagall_events.values()):
            if event.state:
                event.stop()
        self._tagall_events.clear()
        logger.info("Все процессы TagAll остановлены из-за выгрузки модуля.")

    def _get_allowed_chat_ids_map(self) -> dict[int, int]:
        """
        Парсит строку allowed_chat_ids из конфига в словарь {index: chat_id}.
        Индексы 1-основанные.
        """
        allowed_ids_raw = self.config["allowed_chat_ids"]
        allowed_chats_map = {}
        # Очищаем строку от всего, кроме цифр и запятых, затем разбиваем
        cleaned_allowed_ids_raw = re.sub(r"[^0-9,]", "", allowed_ids_raw)  # Оставляем только цифры и запятые
        for i, chat_id_str in enumerate(cleaned_allowed_ids_raw.split(',')):
            chat_id_str = chat_id_str.strip()
            if chat_id_str:
                try:
                    chat_id = int(chat_id_str)
                    allowed_chats_map[i + 1] = chat_id  # 1-based index
                except ValueError:
                    logger.warning(f"Неверный ID чата в конфигурации 'allowed_chat_ids' после очистки: '{chat_id_str}'. Должен быть целым числом.")
        return allowed_chats_map

    def _format_allowed_chats_list(self, allowed_chats_map: dict[int, int]) -> str:
        """Форматирует список разрешенных чатов для вывода."""
        if not allowed_chats_map:
            return "<i>нет</i>"
        return ", ".join([f"<code>{idx}</code>: <code>{chat_id}</code>" for idx, chat_id in sorted(allowed_chats_map.items())])

    async def _resolve_target_chat(self, message: Message, raw_args: str) -> tuple[int | None, str | None]:
        """
        Определяет целевой chat_id для команды, применяя логику allowed_chat_ids и опциональный индекс.
        Возвращает (effective_target_chat_id: int | None, remaining_args: str | None).
        Возвращает None для effective_target_chat_id в случае ошибки.
        """
        original_chat_id = message.chat_id
        effective_target_chat_id = original_chat_id
        remaining_args = raw_args.strip()

        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())

        # Попытка разобрать индекс чата из raw_args
        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            try:
                chat_index = int(chat_index_match.group(1))
                if chat_index in allowed_chats_map:
                    effective_target_chat_id = allowed_chats_map[chat_index]
                    remaining_args = chat_index_match.group(2).strip()
                    if effective_target_chat_id != original_chat_id:
                        await utils.answer(message, self.strings("cmd_redirected_indexed").format(target_chat_id=effective_target_chat_id, index=chat_index))
                    return effective_target_chat_id, remaining_args
                else:
                    await utils.answer(message, self.strings("invalid_chat_index").format(index=chat_index, allowed_chats=self._format_allowed_chats_list(allowed_chats_map)))
                    return None, None
            except ValueError:
                # Недействительный целочисленный индекс, продолжаем обычный разбор аргументов для текущего чата
                pass

        # Если индекс не был предоставлен или был недействительным, применяем существующую логику на основе текущего чата
        if not allowed_chat_ids_set:
            # Если allowed_chat_ids пусто, нет ограничений, команда выполняется в текущем чате
            return original_chat_id, remaining_args

        if original_chat_id in allowed_chat_ids_set:
            # Команда запущена в разрешенном чате
            return original_chat_id, remaining_args
        else:
            # Команда запущена в неразрешенном чате
            if len(allowed_chat_ids_set) == 1:
                # Только один разрешенный чат, перенаправляем туда
                redirect_chat_id = next(iter(allowed_chat_ids_set))
                await utils.answer(message, self.strings("cmd_redirected").format(target_chat_id=redirect_chat_id))
                return redirect_chat_id, remaining_args
            else:
                # Несколько разрешенных чатов, но не текущий, и индекс не указан. Ошибка.
                await utils.answer(message, self.strings("cmd_not_allowed_multiple").format(allowed_chats=self._format_allowed_chats_list(allowed_chats_map)))
                return None, None

    def _get_random_timeout(self, event: StopEvent) -> float:
        """
        Разбирает конфигурацию таймаута и возвращает случайное значение таймаута.
        Поддерживает одно число с плавающей точкой, несколько чисел через запятую или диапазон чисел (например, "0.1-1.0").
        Гарантирует, что один и тот же таймаут не повторяется в двух последовательных вызовах,
        если указано несколько различных значений.
        """
        timeout_str = self.config["timeout"]
        default_timeout = 0.1
        current_timeout = default_timeout

        try:
            # Удаляем все символы, кроме цифр, точек, запятых и дефисов.
            cleaned_timeout_str = re.sub(r"[^0-9.,-]", "", timeout_str).strip()

            if not cleaned_timeout_str:
                logger.warning(f"Пустая строка таймаута. Используется значение по умолчанию {default_timeout}.")
                return default_timeout

            if "," in cleaned_timeout_str:
                values = []
                for part in cleaned_timeout_str.split(','):
                    part = part.strip()
                    if part:
                        try:
                            val = float(part)
                            if val >= 0.0:
                                values.append(val)
                        except ValueError:
                            logger.warning(f"Неверное значение в списке таймаутов: '{part}'. Игнорируется.")

                if values:
                    if len(values) > 1 and event.last_timeout is not None and event.last_timeout in values:
                        available_values = [v for v in values if v != event.last_timeout]
                        if not available_values:  # Если все значения совпадают с last_timeout, берем из всех (повтор допустим)
                            current_timeout = random.choice(values)
                        else:  # Есть другие значения, выбираем из них
                            current_timeout = random.choice(available_values)
                    else:  # Либо одно значение, либо нет last_timeout, либо last_timeout не в списке
                        current_timeout = random.choice(values)
                else:
                    logger.warning(f"Не удалось разобрать значения таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

            elif re.match(r"^\d*\.?\d*-\d*\.?\d*$", cleaned_timeout_str):  # Проверяем формат диапазона X.Y-Z.W
                parts = cleaned_timeout_str.split('-', 1)
                try:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())

                    min_val = max(0.0, min_val)
                    max_val = max(0.0, max_val)

                    if min_val > max_val:
                        min_val, max_val = max_val, min_val

                    current_timeout = random.uniform(min_val, max_val)
                except ValueError:
                    logger.warning(f"Не удалось разобрать диапазон таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

            else:  # Одно значение с плавающей точкой
                try:
                    current_timeout = max(0.0, float(cleaned_timeout_str))
                except ValueError:
                    logger.warning(f"Не удалось разобрать одиночное значение таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

        except Exception as e:
            logger.error(f"Неожиданная ошибка при разборе таймаута '{timeout_str}': {e}. Используется значение по умолчанию {default_timeout}.")

        event.last_timeout = current_timeout
        return current_timeout

    async def _run_tagall_process(self, chat_id: int, message_prefix: str, event: StopEvent, is_trigger: bool = False):
        """Внутренняя функция для обработки основной логики TagAll."""
        # Helper to send messages based on context.
        # For trigger-activated TagAll, messages are sent directly to the chat.
        # For command-activated TagAll, the command itself handles initial `utils.answer` messages,
        # and internal errors are sent directly to chat_id.
        async def send_response(text: str):
            await self._client.send_message(chat_id, text)

        deleted_message_ids_hikkatl = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"Не удалось получить сущность чата для ID {chat_id}: {e}")
            await send_response(f"🚫 <b>Не удалось найти чат с ID:</b> <code>{chat_id}</code>")
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            return

        excluded_user_ids = set()
        exclude_ids_raw = self.config["exclude_user_ids"]
        for uid_str in exclude_ids_raw.split(','):
            uid_str = uid_str.strip()
            if uid_str:
                try:
                    excluded_user_ids.add(int(uid_str))
                except ValueError:
                    logger.warning(f"Неверный ID пользователя в конфигурации 'exclude_user_ids': '{uid_str}'. Должен быть целым числом.")

        if is_bot_sender:
            try:
                # Добавлена проверка на наличие self.inline.bot_client
                if not hasattr(self, 'inline') or not hasattr(self.inline, 'bot_username') or not getattr(self.inline, 'bot_client', None):
                    raise RuntimeError("Инлайн-бот не настроен или недоступен.")

                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):  # Подавляем ошибки, если бот уже в чате или не может быть приглашен
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Не удалось получить сущность бота или пригласить бота: {e}")
                await send_response(self.strings("bot_error"))
                event.stop()
                if chat_id in self._tagall_events:
                    del self._tagall_events[chat_id]
                return

        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                participants.append(user)

        if not participants:
            logger.warning(f"В чате {chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            await send_response(self.strings("no_eligible_participants"))
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            return

        random.shuffle(participants)

        start_time = time.time()

        try:
            first_pass = True
            while self.config["cycle_tagging"] or first_pass:
                if not event.state:
                    break

                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    event.stop()
                    break

                current_participants_for_cycle = []
                if self.config["cycle_tagging"] and not first_pass:
                    logger.debug(f"Повторный запрос участников для цикла в чате {chat_id}.")
                    async for user in self._client.iter_participants(chat_id):
                        if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                            current_participants_for_cycle.append(user)
                    random.shuffle(current_participants_for_cycle)
                    participants = current_participants_for_cycle

                if not participants:
                    logger.warning(f"В чате {chat_id} не найдено участников для TagAll, останавливаем цикл.")
                    break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state:
                        break

                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        event.stop()
                        break

                    tags = []
                    for user in chunk:
                        if user.username:
                            user_display_name = f"@{user.username}"
                        else:
                            display_name_parts = []
                            if user.first_name:
                                display_name_parts.append(user.first_name)
                            if user.last_name:
                                display_name_parts.append(user.last_name)

                            display_name = " ".join(display_name_parts)
                            user_display_name = utils.escape_html(display_name or "Пользователь")

                        tags.append(f'<a href="tg://user?id={user.id}">{user_display_name}</a>')

                    if message_prefix:
                        full_message_text = f"{message_prefix}\n{' '.join(tags)}"
                    else:
                        full_message_text = " ".join(tags)

                    if is_bot_sender:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            m = await self.inline.bot_client.send_message(
                                chat_id,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_bot_client.append(m.id)
                        else:
                            logger.error("Клиент инлайн-бота недоступен или не настроен, переключаемся на юзербота для отправки сообщений.")
                            m = await self._client.send_message(
                                chat_entity,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_hikkatl.append(m.id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(event))

                first_pass = False
                if self.config["cycle_tagging"] and event.state:
                    await asyncio.sleep(self.config["cycle_delay"])
                elif not self.config["cycle_tagging"]:
                    break

        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(chat_entity, chunk_ids)
                        else:
                            logger.warning("Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if event.state:
                logger.info(f"Процесс TagAll завершен естественным образом в чате {chat_id}.")

            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]

    # New message watcher method
    async def _message_watcher(self, message: Message):
        if not self.config["trigger_system_enabled"]: # Check if trigger system is enabled
            return

        if not message.text:
            return

        chat_id = message.chat_id
        sender_id = message.sender_id

        # Get trigger configurations
        start_trigger = self.config["trigger_start_message"].strip().lower()
        stop_trigger = self.config["trigger_stop_message"].strip().lower()
        trigger_chat = self.config["trigger_chat_id"]
        trigger_user = self.config["trigger_user_id"]
        delete_trigger_message = self.config["trigger_delete_message"]

        # Check chat and user conditions
        if trigger_chat != 0 and chat_id != trigger_chat:
            return
        if trigger_user != 0 and sender_id != trigger_user:
            return

        message_text = message.text.lower()

        # Handle start trigger
        if start_trigger and message_text == start_trigger:
            if chat_id in self._tagall_events and self._tagall_events[chat_id].state:
                await self._client.send_message(chat_id, self.strings("trigger_tagall_already_running").format(chat_id=chat_id))
            else:
                event = StopEvent(chat_id)
                self._tagall_events[chat_id] = event
                # Run tagall without prefix for trigger, and mark as trigger activation
                self._client.loop.create_task(self._run_tagall_process(chat_id, "", event, is_trigger=True))
                await self._client.send_message(chat_id, self.strings("trigger_tagall_started").format(chat_id=chat_id))
            if delete_trigger_message and message.out: # Delete if it's our own message
                await message.delete()
            return

        # Handle stop trigger
        if stop_trigger and message_text == stop_trigger:
            event = self._tagall_events.get(chat_id)
            if event and event.state:
                event.stop()
                await self._client.send_message(chat_id, self.strings("trigger_tagall_stopped").format(chat_id=chat_id))
            else:
                await self._client.send_message(chat_id, self.strings("trigger_tagall_not_running").format(chat_id=chat_id))
            if delete_trigger_message and message.out: # Delete if it's our own message
                await message.delete()
            return

    @loader.command(
        groups=True,
        ru_doc=lambda self: self.strings("_cmd_tagall_doc"),
        de_doc=lambda self: self.strings("_cmd_tagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_tagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_tagall_doc"),
    )
    async def tagall(self, message: Message):
        """[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги."""
        raw_args = utils.get_args_raw(message)
        target_chat_id, message_prefix = await self._resolve_target_chat(message, raw_args)

        if target_chat_id is None:  # Ошибка при разрешении чата
            if message.out:
                await message.delete()
            return

        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            await utils.answer(message, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            if message.out:
                await message.delete()
            return

        # Если команда была исходящей, удаляем ее, чтобы не засорять чат
        if message.out:
            await message.delete()

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event

        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix, event, is_trigger=False)) # Explicitly not a trigger

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        de_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
    )
    async def stoptagall(self, message: Message):
        """[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>."""
        raw_args = utils.get_args_raw(message)
        target_chat_id, _ = await self._resolve_target_chat(message, raw_args)

        if target_chat_id is None:  # Ошибка при разрешении чата
            if message.out:
                await message.delete()
            return

        event = self._tagall_events.get(target_chat_id)

        if event and event.state:
            event.stop()
            # Respond to the command directly
            await utils.answer(message, self.strings("trigger_tagall_stopped").format(chat_id=target_chat_id)) # Use stopped string as it's clear
        else:
            await utils.answer(message, self.strings("tagall_not_running").format(chat_id=target_chat_id))

        # Если команда была исходящей, удаляем ее, чтобы не засорять чат
        if message.out:
            await message.delete()

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        de_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_autotagall_doc"),
    )
    async def autotagall(self, message: Message):
        """[on|off|true|false] - Включить/выключить систему триггеров. Без аргументов - переключить текущее состояние."""
        args = utils.get_args(message)
        
        # Check if command can be used in this chat
        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())
        
        # if allowed_chat_ids is not empty, check if current chat is allowed or if there's a single redirect target
        if allowed_chat_ids_set and message.chat_id not in allowed_chat_ids_set:
            if len(allowed_chat_ids_set) == 1:
                # Redirect if only one allowed chat, but we don't redirect for autotagall as it's global.
                # Just prevent usage if not in the single allowed chat.
                await utils.answer(message, self.strings("cmd_not_allowed_current"))
            else:
                # Multiple allowed chats, and current is not one of them.
                await utils.answer(message, self.strings("cmd_not_allowed_multiple").format(allowed_chats=self._format_allowed_chats_list(allowed_chats_map)))
            if message.out:
                await message.delete()
            return

        current_state = self.config["trigger_system_enabled"]
        new_state = current_state

        if not args:
            # Toggle state
            new_state = not current_state
        else:
            arg = args[0].lower()
            if arg in ["on", "true"]:
                new_state = True
            elif arg in ["off", "false"]:
                new_state = False
            else:
                await utils.answer(message, self.strings("invalid_autotagall_arg"))
                if message.out:
                    await message.delete()
                return

        self.config["trigger_system_enabled"] = new_state
        if new_state:
            await utils.answer(message, self.strings("triggers_enabled"))
        else:
            await utils.answer(message, self.strings("triggers_disabled"))

        if message.out:
            await message.delete()
