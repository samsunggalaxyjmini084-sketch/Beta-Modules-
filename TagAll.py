# meta developer: @NKDebra
# meta name: TagAll
# meta version: 2.0.41
#
# 01101110 01100101 01110110 01100101 01110010 00100000 01100111 01101001 01110110 01100101 00100000 01110101 01110000
# 01101110 01100101 01110110 01100101 01110010 00100000 01101100 01100101 01110100 00100000 01111001 01101111 01110101 00100000 01100100 01101111 01110111 01101110
# 01101110 01100101 01110110 01100101 01110010 00100000 01110010 01110101 01101110 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01100100 01100101 01110011 01100101 01110010 01110100 00100000 01111001 01101111 01110101
# 01101110 01100101 01110110 01100101 01110010 00100000 01101101 01100001 01101011 01100101 00100000 01111001 01101111 01110101 00100000 01100011 01110010 01111001 00100000 01101110 01100101 01110110 01100101 01110010 00100000 01110011 01100001 01111001 00100000 01100111 01101111 01101111 01100100 01100010 01111001 01100101
# 01101110 01100101 01110110 01100101 01110010 00100000 01110100 01100101 01101100 00100000 01100001 01101100 01101100 00100000 01100001 00100000 01101100 01101001 01100101 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 00100000 01101000 01110101 01110010 01111001 01101111 01110101
# (Rick Astley - Never Gonna Give You Up)

import asyncio
import contextlib
import logging
import random
import time
import re

# Заменены импорты hikkatl на telethon
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import Message
from telethon import events  # Добавлен импорт событий

# Эти импорты предполагают, что модуль запускается в userbot-фреймворке,
# который предоставляет 'loader' и 'utils' (возможно, на базе Telethon).
# Если это не так, эти строки потребуют адаптации к целевой среде.
from .. import loader, utils

logger = logging.getLogger(__name__)


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
        "_cfg_doc_silent": (
            "Если включено, при активации TagAll через триггер, не будет отправлено"
            " подтверждающее сообщение о начале/остановке TagAll."
        ),
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя команду .stoptagall"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Сколько пользователей тегать в одном сообщении",
        "_cfg_doc_duration": "Как долго (в секундах) должен работать процесс TagAll. Установите 0 для неограниченного времени.",
        "_cfg_doc_trigger_message": "Сообщение-триггер для запуска TagAll. Если сообщение пользователя содержит этот текст (регистронезависимо), TagAll будет запущен.",
        "_cfg_doc_trigger_message_stop": "Сообщение-триггер для остановки TagAll. Если сообщение пользователя содержит этот текст (регистронезависимо), TagAll будет остановлен.",
        "_cfg_doc_trigger_user_ids": (
            "ID пользователя(ей), которые могут активировать TagAll с помощью триггеров."
            " Разделяйте запятыми. Если пусто, любой пользователь может использовать триггеры."
        ),
        "_cfg_doc_triggers_enabled": "Включает или выключает общую работу системы триггеров TagAll.", # NEW STRING
        "_cfg_doc_exclude_user_ids": "ID пользователя(ей), которых не нужно тегать. Разделяйте запятыми. Например: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "ID чата(ов), в которых разрешено использовать команды модуля TagAll. Разделяйте запятыми. Если указан только один ID, команды, запущенные в других чатах, будут автоматически перенаправлены в этот чат. Если пусто, команды разрешены во всех чатах.",
        "_cmd_tagall_doc": "[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        "_cmd_stoptagall_doc": "[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>.",
        "_cmd_triggers_doc": "[on|off] - Включить или выключить работу триггеров для TagAll.", # NEW STRING
        "tagall_not_running": "🚫 <b>TagAll в данный момент не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}. Используйте <code>.stoptagall</code>, чтобы остановить его.</b>",
        "no_eligible_participants": "🚫 <b>В этом чате нет подходящих участников для тега.</b>",
        "cmd_redirected": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code>, так как он единственный разрешенный.",
        "cmd_not_allowed": "🚫 <b>Эта команда не может быть использована в текущем чате, и нет единственного разрешенного чата для перенаправления.</b>",
        "cmd_not_allowed_current": "🚫 <b>Эта команда не может быть использована в текущем чате.</b>",
        "cmd_redirected_indexed": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code> (индекс <code>{index}</code>).",
        "invalid_chat_index": "🚫 <b>Неверный индекс чата</b> <code>{index}</code>. Разрешенные чаты: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Эта команда не может быть использована в текущем чате. Укажите индекс чата или используйте в одном из разрешенных чатов:</b> {allowed_chats}.",
        "trigger_activated_start": "✅ <b>TagAll запущен триггером в чате {chat_id}.</b>",
        "trigger_activated_stop": "✅ <b>TagAll остановлен триггером в чате {chat_id}.</b>",
        "trigger_not_allowed_chat": "🚫 <b>Триггеры TagAll не разрешены в чате {chat_id}.</b>",
        "triggers_status": "⚙️ <b>Триггеры TagAll:</b> {status}", # NEW STRING
        "triggers_status_on": "включены", # NEW STRING
        "triggers_status_off": "выключены", # NEW STRING
        "triggers_invalid_arg": "🚫 <b>Неверный аргумент. Используйте 'on' или 'off'.</b>", # NEW STRING
        "triggers_already_in_state": "ℹ️ <b>Триггеры TagAll уже {state}.</b>", # NEW STRING
        "triggers_state_changed": "✅ <b>Триггеры TagAll теперь {new_state}.</b>", # NEW STRING
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
        "_cfg_doc_silent": (
            "Wenn aktiviert, wird beim Starten von TagAll durch einen Trigger keine"
            " Bestätigungsnachricht über den Start/Stop von TagAll gesendet."
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
        "_cfg_doc_trigger_message": "Trigger-Nachricht zum Starten von TagAll. Wenn die Nachricht des Benutzers diesen Text enthält (Groß-/Kleinschreibung wird nicht beachtet), wird TagAll gestartet.",
        "_cfg_doc_trigger_message_stop": "Trigger-Nachricht zum Stoppen von TagAll. Wenn die Nachricht des Benutzers diesen Text enthält (Groß-/Kleinschreibung wird nicht beachtet), wird TagAll gestoppt.",
        "_cfg_doc_trigger_user_ids": (
            "Benutzer-ID(s), die TagAll mit Triggern aktivieren können."
            " Durch Kommas getrennt eingeben. Wenn leer, kann jeder Benutzer Trigger verwenden."
        ),
        "_cfg_doc_triggers_enabled": "Aktiviert oder deaktiviert die allgemeine Funktion des TagAll-Trigger-Systems.", # NEW STRING
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht in Chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits in Chat {chat_id}. Verwenden Sie <code>.stoptagall</code>, um es zu stoppen.</b>",
        "_cfg_doc_exclude_user_ids": "Benutzer-ID(s), die nicht erwähnt werden sollen. Kommagetrennt eingeben. Zum Beispiel: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "Chat-ID(s), in denen die TagAll-Modulbefehle verwendet werden dürfen. Durch Kommas getrennt eingeben. Wenn nur eine ID angegeben ist, werden Befehle, die in anderen Chats ausgeführt werden, automatisch in diesen Chat umgeleitet. Wenn leer, sind Befehle in allen Chats erlaubt.",
        "_cmd_tagall_doc": "[<Chat-Nummer>] [Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet.",
        "_cmd_stoptagall_doc": "[<Chat-Nummer>] - Den laufenden TagAll-Prozess im <b>angegebenen oder aktuellen Chat</b> stoppen.",
        "_cmd_triggers_doc": "[on|off] - Aktiviert oder deaktiviert die Trigger-Funktion für TagAll.", # NEW STRING
        "no_eligible_participants": "🚫 <b>In diesem Chat gibt es keine geeigneten Teilnehmer zum Taggen.</b>",
        "cmd_redirected": "➡️ <b>Befehl wurde in Chat</b> <code>{target_chat_id}</code> umgeleitet, da dies der einzige erlaubte ist.",
        "cmd_not_allowed": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden, und es gibt keinen einzigen erlaubten Chat zur Umleitung.</b>",
        "cmd_not_allowed_current": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden.</b>",
        "cmd_redirected_indexed": "➡️ <b>Befehl wurde in Chat</b> <code>{target_chat_id}</code> (Index <code>{index}</code>) umgeleitet.",
        "invalid_chat_index": "🚫 <b>Ungültiger Chat-Index</b> <code>{index}</code>. Erlaubte Chats: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden. Geben Sie einen Chat-Index an oder verwenden Sie ihn in einem der erlaubten Chats:</b> {allowed_chats}.",
        "trigger_activated_start": "✅ <b>TagAll wurde durch einen Trigger in Chat {chat_id} gestartet.</b>",
        "trigger_activated_stop": "✅ <b>TagAll wurde durch einen Trigger in Chat {chat_id} gestoppt.</b>",
        "trigger_not_allowed_chat": "🚫 <b>TagAll-Trigger sind in Chat {chat_id} nicht erlaubt.</b>",
        "triggers_status": "⚙️ <b>TagAll Trigger:</b> {status}", # NEW STRING
        "triggers_status_on": "aktiviert", # NEW STRING
        "triggers_status_off": "deaktiviert", # NEW STRING
        "triggers_invalid_arg": "🚫 <b>Ungültiges Argument. Verwenden Sie 'on' oder 'off'.</b>", # NEW STRING
        "triggers_already_in_state": "ℹ️ <b>TagAll Trigger sind bereits {state}.</b>", # NEW STRING
        "triggers_state_changed": "✅ <b>TagAll Trigger sind jetzt {new_state}.</b>", # NEW STRING
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
        "_cfg_doc_silent": (
            "Etkinleştirilirse, TagAll bir tetikleyici ile başlatıldığında,"
            " TagAll'un başlatıldığı/durdurulduğu hakkında bir onay mesajı gönderilmeyecektir."
        ),
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Bir mesajda kaç kullanıcı etiketlenecek",
        "_cfg_doc_duration": "TagAll sürecinin ne kadar süre (saniye) çalışması gerektiği. Sınırsız süre için 0 olarak ayarlayın.",
        "_cfg_doc_trigger_message": "TagAll'u başlatmak için tetikleyici mesaj. Kullanıcının mesajı bu metni içeriyorsa (büyük/küçük harf duyarsız), TagAll başlatılır.",
        "_cfg_doc_trigger_message_stop": "TagAll'u durdurmak için tetikleyici mesaj. Kullanıcının mesajı bu metni içeriyorsa (büyük/küçük harf duyarsız), TagAll durdurulur.",
        "_cfg_doc_trigger_user_ids": (
            "TagAll'u tetikleyicilerle etkinleştirebilecek kullanıcı kimliği(leri)."
            " Virgülle ayırın. Boş bırakılırsa, herhangi bir kullanıcı tetikleyici kullanabilir."
        ),
        "_cfg_doc_triggers_enabled": "TagAll tetikleyici sisteminin genel çalışmasını açar veya kapatır.", # NEW STRING
        "_cfg_doc_exclude_user_ids": "Etiketlenmeyecek kullanıcı kimliği(leri). Virgülle ayırın. Örneğin: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "TagAll modül komutlarının kullanılabileceği sohbet kimliği(leri). Virgülle ayırın. Yalnızca bir kimlik belirtilirse, diğer sohbetlerde başlatılan komutlar otomatik olarak bu sohbete yönlendirilecektir. Boş bırakılırsa, komutlara tüm sohbetlerde izin verilir.",
        "_cmd_tagall_doc": "[<Sohbet Numarası>] [metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir.",
        "_cmd_stoptagall_doc": "[<Sohbet Numarası>] - Çalışan TagAll sürecini <b>belirtilen veya mevcut sohbette</b> durdur.",
        "_cmd_triggers_doc": "[on|off] - TagAll için tetikleyicilerin çalışmasını açar veya kapatır.", # NEW STRING
        "tagall_not_running": "🚫 <b>TagAll şu anda {chat_id} sohbetinde çalışmıyor.</b>",
        "tagall_already_running": "🚫 <b>TagAll zaten {chat_id} sohbetinde çalışıyor. Durdurmak için <code>.stoptagall</code> komutunu kullanın.</b>",
        "no_eligible_participants": "🚫 <b>Bu sohbette etiketlenecek uygun katılımcı yok.</b>",
        "cmd_redirected": "➡️ <b>Komut, izin verilen tek sohbet olduğu için</b> <code>{target_chat_id}</code> sohbetine yönlendirildi.",
        "cmd_not_allowed": "🚫 <b>Bu komut mevcut sohbette kullanılamaz ve yönlendirmek için tek bir izin verilen sohbet yok.</b>",
        "cmd_not_allowed_current": "🚫 <b>Bu komut mevcut sohbette kullanılamaz.</b>",
        "cmd_redirected_indexed": "➡️ <b>Komut,</b> <code>{target_chat_id}</code> (dizin <code>{index}</code>) sohbetine yönlendirildi.",
        "invalid_chat_index": "🚫 <b>Geçersiz sohbet dizini</b> <code>{index}</code>. İzin verilen sohbetler: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Bu komut mevcut sohbette kullanılamaz. Bir sohbet dizini belirtin veya izin verilen sohbetlerden birinde kullanın:</b> {allowed_chats}.",
        "trigger_activated_start": "✅ <b>TagAll, {chat_id} sohbetinde bir tetikleyici tarafından başlatıldı.</b>",
        "trigger_activated_stop": "✅ <b>TagAll, {chat_id} sohbetinde bir tetikleyici tarafından durduruldu.</b>",
        "trigger_not_allowed_chat": "🚫 <b>TagAll tetikleyicilerine {chat_id} sohbetinde izin verilmiyor.</b>",
        "triggers_status": "⚙️ <b>TagAll Tetikleyicileri:</b> {status}", # NEW STRING
        "triggers_status_on": "açık", # NEW STRING
        "triggers_status_off": "kapalı", # NEW STRING
        "triggers_invalid_arg": "🚫 <b>Geçersiz argüman. 'on' veya 'off' kullanın.</b>", # NEW STRING
        "triggers_already_in_state": "ℹ️ <b>TagAll Tetikleyicileri zaten {state}.</b>", # NEW STRING
        "triggers_state_changed": "✅ <b>TagAll Tetikleyicileri artık {new_state}.</b>", # NEW STRING
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
        "_cfg_doc_silent": (
            "Agar yoqilgan bo'lsa, TagAll trigger orqali ishga tushirilganda,"
            " TagAllning boshlanishi/to'xtashi haqida tasdiqlovchi xabar yuborilmaydi."
        ),
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi etiketlanadi",
        "_cfg_doc_duration": "TagAll jarayoni qancha vaqt (soniya) ishlashi kerak. Cheksiz vaqt uchun 0 ga o'rnating.",
        "_cfg_doc_trigger_message": "TagAll'ni ishga tushirish uchun trigger xabar. Agar foydalanuvchi xabari bu matnni o'z ichiga olsa (katta/kichik harflar ahamiyatsiz), TagAll ishga tushiriladi.",
        "_cfg_doc_trigger_message_stop": "TagAll'ni to'xtatish uchun trigger xabar. Agar foydalanuvchi xabari bu matnni o'z ichiga olsa (katta/kichik harflar ahamiyatsiz), TagAll to'xtatiladi.",
        "_cfg_doc_trigger_user_ids": (
            "Triggerlar yordamida TagAll'ni faollashtirishi mumkin bo'lgan foydalanuvchi ID(lar)i."
            " Vergul bilan ajrating. Agar bo'sh bo'lsa, har qanday foydalanuvchi triggerlardan foydalanishi mumkin."
        ),
        "_cfg_doc_triggers_enabled": "TagAll trigger tizimining umumiy ishini yoqadi yoki o'chiradi.", # NEW STRING
        "_cfg_doc_exclude_user_ids": "Etiketlanmaydigan foydalanuvchi ID(lar)i. Vergul bilan ajrating. Misol uchun: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "TagAll modul buyruqlaridan foydalanishga ruxsat berilgan chat ID(lar)i. Vergul bilan ajrating. Agar faqat bitta ID ko'rsatilgan bo'lsa, boshqa chatlarda ishga tushirilgan buyruqlar avtomatik ravishda ushbu chatga yo'naltiriladi. Bo'sh bo'lsa, buyruqlarga barcha chatlarda ruxsat beriladi.",
        "_cmd_tagall_doc": "[<Chat raqami>] [matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi.",
        "_cmd_stoptagall_doc": "[<Chat raqami>] - Ishlayotgan TagAll jarayonini <b>ko'rsatilgan yoki joriy chatda</b> to'xtatish.",
        "_cmd_triggers_doc": "[on|off] - TagAll uchun triggerlarning ishlashini yoqish yoki o'chirish.", # NEW STRING
        "tagall_not_running": "🚫 <b>TagAll hozirda {chat_id} chatida ishlamayapti.</b>",
        "tagall_already_running": "🚫 <b>TagAll {chat_id} chatida allaqachon ishlamoqda. Uni to'xtatish uchun <code>.stoptagall</code> dan foydalaning.</b>",
        "no_eligible_participants": "🚫 <b>Bu chatda tegish uchun mos ishtirokchilar topilmadi.</b>",
        "cmd_redirected": "➡️ <b>Buyruq, ruxsat berilgan yagona chat bo'lgani uchun</b> <code>{target_chat_id}</code> chatiga yo'naltirildi.",
        "cmd_not_allowed": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi va yo'naltirish uchun yagona ruxsat berilgan chat yo'q.</b>",
        "cmd_not_allowed_current": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi.</b>",
        "cmd_redirected_indexed": "➡️ <b>Buyruq,</b> <code>{target_chat_id}</code> (dizin <code>{index}</code>) chatiga yo'naltirildi.",
        "invalid_chat_index": "🚫 <b>Noto'g'ri chat indeksi</b> <code>{index}</code>. Ruxsat berilgan chatlar: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi. Chat indeksini ko'rsating yoki ruxsat berilgan chatlardan birida foydalaning:</b> {allowed_chats}.",
        "trigger_activated_start": "✅ <b>TagAll {chat_id} chatida trigger tomonidan ishga tushirildi.</b>",
        "trigger_activated_stop": "✅ <b>TagAll {chat_id} chatida trigger tomonidan to'xtatildi.</b>",
        "trigger_not_allowed_chat": "🚫 <b>TagAll triggerlariga {chat_id} chatida ruxsat berilmaydi.</b>",
        "triggers_status": "⚙️ <b>TagAll Triggerlari:</b> {status}", # NEW STRING
        "triggers_status_on": "yoqilgan", # NEW STRING
        "triggers_status_off": "o'chirilgan", # NEW STRING
        "triggers_invalid_arg": "🚫 <b>Noto'g'ri argument. 'on' yoki 'off' dan foydalaning.</b>", # NEW STRING
        "triggers_already_in_state": "ℹ️ <b>TagAll Triggerlari allaqachon {state}.</b>", # NEW STRING
        "triggers_state_changed": "✅ <b>TagAll Triggerlari endi {new_state}.</b>", # NEW STRING
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
                "silent",
                False,
                lambda: self.strings("_cfg_doc_silent"),
                validator=loader.validators.Boolean(),
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
                "trigger_message",
                "",
                lambda: self.strings("_cfg_doc_trigger_message"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "trigger_message_stop",
                "",
                lambda: self.strings("_cfg_doc_trigger_message_stop"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "trigger_user_ids",
                "",
                lambda: self.strings("_cfg_doc_trigger_user_ids"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue( # NEW: triggers_enabled
                "triggers_enabled",
                True,
                lambda: self.strings("_cfg_doc_triggers_enabled"),
                validator=loader.validators.Boolean(),
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
        )
        self._tagall_processes: dict[int, dict] = {}
        self._message_watcher_handler = None

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        if not self._message_watcher_handler:
            self._message_watcher_handler = self._client.add_event_handler(
                self._message_watcher, events.NewMessage(incoming=True, func=lambda m: bool(m.text))
            )

    async def on_unload(self):
        if self._client and self._message_watcher_handler:
            self._client.remove_event_handler(self._message_watcher_handler)
            self._message_watcher_handler = None

        for process_data in list(self._tagall_processes.values()):
            task = process_data.get("task")
            if task and not task.done():
                task.cancel()
        self._tagall_processes.clear()
        logger.info("Все процессы TagAll остановлены из-за выгрузки модуля.")

    def _get_allowed_chat_ids_map(self) -> dict[int, int]:
        """
        Парсит строку allowed_chat_ids из конфига в словарь {index: chat_id}.
        Индексы 1-основанные.
        """
        allowed_ids_raw = self.config["allowed_chat_ids"]
        allowed_chats_map = {}
        cleaned_allowed_ids_raw = re.sub(r"[^0-9,]", "", allowed_ids_raw)
        for i, chat_id_str in enumerate(cleaned_allowed_ids_raw.split(",")):
            chat_id_str = chat_id_str.strip()
            if chat_id_str:
                try:
                    chat_id = int(chat_id_str)
                    allowed_chats_map[i + 1] = chat_id
                except ValueError:
                    logger.warning(
                        f"Неверный ID чата в конфигурации 'allowed_chat_ids' после очистки: '{chat_id_str}'. Должен быть целым числом."
                    )
        return allowed_chats_map

    def _is_chat_allowed_for_trigger(self, chat_id: int) -> bool:
        """
        Проверяет, разрешен ли данный чат для активации триггеров.
        Если allowed_chat_ids пуст, разрешено во всех чатах.
        """
        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())

        if not allowed_chat_ids_set:
            return True

        return chat_id in allowed_chat_ids_set

    def _format_allowed_chats_list(self, allowed_chats_map: dict[int, int]) -> str:
        """Форматирует список разрешенных чатов для вывода."""
        if not allowed_chats_map:
            return "<i>нет</i>"
        return ", ".join(
            [f"<code>{idx}</code>: <code>{chat_id}</code>" for idx, chat_id in sorted(allowed_chats_map.items())]
        )

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

        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            try:
                chat_index = int(chat_index_match.group(1))
                if chat_index in allowed_chats_map:
                    effective_target_chat_id = allowed_chats_map[chat_index]
                    remaining_args = chat_index_match.group(2).strip()
                    if effective_target_chat_id != original_chat_id:
                        await utils.answer(
                            message,
                            self.strings("cmd_redirected_indexed").format(
                                target_chat_id=effective_target_chat_id, index=chat_index
                            ),
                        )
                    return effective_target_chat_id, remaining_args
                else:
                    await utils.answer(
                        message,
                        self.strings("invalid_chat_index").format(
                            index=chat_index, allowed_chats=self._format_allowed_chats_list(allowed_chats_map)
                        ),
                    )
                    return None, None
            except ValueError:
                pass

        if not allowed_chat_ids_set:
            return original_chat_id, remaining_args

        if original_chat_id in allowed_chat_ids_set:
            return original_chat_id, remaining_args
        else:
            if len(allowed_chat_ids_set) == 1:
                redirect_chat_id = next(iter(allowed_chat_ids_set))
                await utils.answer(message, self.strings("cmd_redirected").format(target_chat_id=redirect_chat_id))
                return redirect_chat_id, remaining_args
            else:
                await utils.answer(
                    message,
                    self.strings("cmd_not_allowed_multiple").format(
                        allowed_chats=self._format_allowed_chats_list(allowed_chats_map)
                    ),
                )
                return None, None

    def _get_random_timeout(self, chat_id: int) -> float:
        """
        Разбирает конфигурацию таймаута и возвращает случайное значение таймаута.
        Поддерживает одно число с плавающей точкой, несколько чисел через запятую или диапазон чисел (например, "0.1-1.0").
        Гарантирует, что один и тот же таймаут не повторяется в двух последовательных вызовах,
        если указано несколько различных значений.
        """
        timeout_str = self.config["timeout"]
        default_timeout = 0.1
        current_timeout = default_timeout

        timeout_data = self._tagall_processes.setdefault(chat_id, {})
        last_timeout = timeout_data.get("last_timeout")

        try:
            cleaned_timeout_str = re.sub(r"[^0-9.,-]", "", timeout_str).strip()

            if not cleaned_timeout_str:
                logger.warning(f"Пустая строка таймаута. Используется значение по умолчанию {default_timeout}.")
                return default_timeout

            if "," in cleaned_timeout_str:
                values = []
                for part in cleaned_timeout_str.split(","):
                    part = part.strip()
                    if part:
                        try:
                            val = float(part)
                            if val >= 0.0:
                                values.append(val)
                        except ValueError:
                            logger.warning(f"Неверное значение в списке таймаутов: '{part}'. Игнорируется.")

                if values:
                    if len(values) > 1 and last_timeout is not None and last_timeout in values:
                        available_values = [v for v in values if v != last_timeout]
                        if not available_values:
                            current_timeout = random.choice(values)
                        else:
                            current_timeout = random.choice(available_values)
                    else:
                        current_timeout = random.choice(values)
                else:
                    logger.warning(
                        f"Не удалось разобрать значения таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}."
                    )

            elif re.match(r"^\d*\.?\d*-\d*\.?\d*$", cleaned_timeout_str):
                parts = cleaned_timeout_str.split("-", 1)
                try:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())

                    min_val = max(0.0, min_val)
                    max_val = max(0.0, max_val)

                    if min_val > max_val:
                        min_val, max_val = max_val, min_val

                    current_timeout = random.uniform(min_val, max_val)
                except ValueError:
                    logger.warning(
                        f"Не удалось разобрать диапазон таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}."
                    )

            else:
                try:
                    current_timeout = max(0.0, float(cleaned_timeout_str))
                except ValueError:
                    logger.warning(
                        f"Не удалось разобрать одиночное значение таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}."
                    )

        except Exception as e:
            logger.error(
                f"Неожиданная ошибка при разборе таймаута '{timeout_str}': {e}. Используется значение по умолчанию {default_timeout}."
            )

        timeout_data["last_timeout"] = current_timeout
        return current_timeout

    async def _message_watcher(self, message: Message):
        """Обработчик входящих сообщений для активации/деактивации TagAll через триггеры."""
        # NEW: Проверяем глобальный статус триггеров
        if not self.config["triggers_enabled"]:
            logger.debug(f"Триггеры TagAll глобально выключены, игнорируем сообщение.")
            return

        if not message.text or not message.chat_id:
            return

        chat_id = message.chat_id
        sender_id = message.sender_id
        message_text_lower = message.text.lower()

        if not self._is_chat_allowed_for_trigger(chat_id):
            logger.debug(f"Триггер TagAll игнорирован в чате {chat_id}: чат не разрешен.")
            return

        allowed_trigger_user_ids_raw = self.config["trigger_user_ids"]
        if allowed_trigger_user_ids_raw:
            allowed_trigger_user_ids = set()
            for uid_str in allowed_trigger_user_ids_raw.split(","):
                uid_str = uid_str.strip()
                if uid_str:
                    try:
                        allowed_trigger_user_ids.add(int(uid_str))
                    except ValueError:
                        logger.warning(
                            f"Неверный ID пользователя в конфигурации 'trigger_user_ids': '{uid_str}'. Игнорируется."
                        )

            if sender_id not in allowed_trigger_user_ids:
                logger.debug(
                    f"Триггер TagAll игнорирован в чате {chat_id}: отправитель {sender_id} не разрешен."
                )
                return

        trigger_start_message = self.config["trigger_message"].lower()
        trigger_stop_message = self.config["trigger_message_stop"].lower()

        tagall_running = chat_id in self._tagall_processes and not self._tagall_processes[chat_id]["task"].done()

        if trigger_start_message and trigger_start_message in message_text_lower:
            if tagall_running:
                logger.debug(f"Триггер запуска TagAll в чате {chat_id} проигнорирован: TagAll уже запущен.")
            else:
                logger.info(f"TagAll запущен триггером '{trigger_start_message}' в чате {chat_id}.")
                task = self._client.loop.create_task(self._run_tagall_process(chat_id, message.text))
                self._tagall_processes[chat_id] = {"task": task, "last_timeout": None}
                if not self.config["silent"]:
                    await self._client.send_message(chat_id, self.strings("trigger_activated_start").format(chat_id=chat_id))

        elif trigger_stop_message and trigger_stop_message in message_text_lower:
            if not tagall_running:
                logger.debug(f"Триггер остановки TagAll в чате {chat_id} проигнорирован: TagAll не запущен.")
            else:
                logger.info(f"TagAll остановлен триггером '{trigger_stop_message}' в чате {chat_id}.")
                process_data = self._tagall_processes.get(chat_id)
                if process_data and not process_data["task"].done():
                    process_data["task"].cancel()
                    if not self.config["silent"]:
                        await self._client.send_message(chat_id, self.strings("trigger_activated_stop").format(chat_id=chat_id))

    async def _run_tagall_process(self, chat_id: int, message_prefix: str):
        """Внутренняя функция для обработки основной логики TagAll."""
        deleted_message_ids_telethon = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"Не удалось получить сущность чата для ID {chat_id}: {e}")
            await self._client.send_message(chat_id, f"🚫 <b>Не удалось найти чат с ID:</b> <code>{chat_id}</code>")
            return

        excluded_user_ids = set()
        exclude_ids_raw = self.config["exclude_user_ids"]
        for uid_str in exclude_ids_raw.split(","):
            uid_str = uid_str.strip()
            if uid_str:
                try:
                    excluded_user_ids.add(int(uid_str))
                except ValueError:
                    logger.warning(
                        f"Неверный ID пользователя в конфигурации 'exclude_user_ids': '{uid_str}'. Должен быть целым числом."
                    )

        if is_bot_sender:
            try:
                if (
                    not hasattr(self, "inline")
                    or not hasattr(self.inline, "bot_username")
                    or not getattr(self.inline, "bot_client", None)
                ):
                    raise RuntimeError("Инлайн-бот не настроен или недоступен в текущей конфигурации.")

                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Не удалось получить сущность бота или пригласить бота: {e}")
                await self._client.send_message(chat_id, self.strings("bot_error"))
                return

        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                participants.append(user)

        if not participants:
            logger.warning(f"В чате {chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            await self._client.send_message(chat_id, self.strings("no_eligible_participants"))
            return

        random.shuffle(participants)

        start_time = time.time()

        try:
            first_pass = True
            while self.config["cycle_tagging"] or first_pass:
                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    logger.info(f"TagAll process for chat {chat_id} finished due to duration limit.")
                    break

                current_participants_for_cycle = []
                if self.config["cycle_tagging"] and not first_pass:
                    logger.debug(f"Повторный запрос участников для цикла в чате {chat_id}.")
                    async for user in self._client.iter_participants(chat_id):
                        if (
                            not user.bot
                            and not user.deleted
                            and user.id != owner_id
                            and user.id not in excluded_user_ids
                        ):
                            current_participants_for_cycle.append(user)
                    random.shuffle(current_participants_for_cycle)
                    participants = current_participants_for_cycle

                if not participants:
                    logger.warning(f"В чате {chat_id} не найдено участников для TagAll, останавливаем цикл.")
                    break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        logger.info(f"TagAll process for chat {chat_id} finished due to duration limit (mid-cycle).")
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
                        if hasattr(self, "inline") and hasattr(self.inline, "bot_client") and self.inline.bot_client:
                            m = await self.inline.bot_client.send_message(
                                chat_id,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_bot_client.append(m.id)
                        else:
                            logger.error(
                                "Клиент инлайн-бота недоступен или не настроен, переключаемся на юзербота для отправки сообщений."
                            )
                            m = await self._client.send_message(
                                chat_entity,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_telethon.append(m.id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_telethon.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(chat_id))

                first_pass = False
                if self.config["cycle_tagging"]:
                    await asyncio.sleep(self.config["cycle_delay"])
                else:
                    break

        except asyncio.CancelledError:
            logger.info(f"TagAll process for chat {chat_id} was cancelled.")
        except Exception as e:
            logger.error(f"Неожиданная ошибка в _run_tagall_process для чата {chat_id}: {e}", exc_info=True)
            with contextlib.suppress(Exception):
                await self._client.send_message(chat_id, f"🚫 <b>Произошла ошибка во время TagAll:</b> <code>{e}</code>")
        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_telethon:
                        for chunk_ids in utils.chunks(deleted_message_ids_telethon, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if hasattr(self, "inline") and hasattr(self.inline, "bot_client") and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(chat_entity, chunk_ids)
                        else:
                            logger.warning("Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if chat_id in self._tagall_processes:
                del self._tagall_processes[chat_id]
                logger.info(f"TagAll process for chat {chat_id} cleaned up from tracking dictionary.")

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

        if target_chat_id is None:
            if message.out:
                await message.delete()
            return

        if target_chat_id in self._tagall_processes and not self._tagall_processes[target_chat_id]["task"].done():
            await utils.answer(message, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            if message.out:
                await message.delete()
            return

        if message.out:
            await message.delete()

        task = self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix))
        self._tagall_processes[target_chat_id] = {"task": task, "last_timeout": None}

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

        if target_chat_id is None:
            if message.out:
                await message.delete()
            return

        process_data = self._tagall_processes.get(target_chat_id)

        if process_data and not process_data["task"].done():
            process_data["task"].cancel()
            logger.info(f"Команда stoptagall: процесс TagAll для чата {target_chat_id} был отменен.")
            await utils.answer(message, f"✅ <b>TagAll в чате {target_chat_id} остановлен.</b>")
        else:
            await utils.answer(message, self.strings("tagall_not_running").format(chat_id=target_chat_id))

        if message.out:
            await message.delete()

    @loader.command( # NEW COMMAND
        ru_doc=lambda self: self.strings("_cmd_triggers_doc"),
        de_doc=lambda self: self.strings("_cmd_triggers_doc"),
        tr_doc=lambda self: self.strings("_cmd_triggers_doc"),
        uz_doc=lambda self: self.strings("_cmd_triggers_doc"),
    )
    async def triggers(self, message: Message):
        """[on|off] - Включить или выключить работу триггеров для TagAll."""
        args = utils.get_args_raw(message).lower()
        current_state = self.config["triggers_enabled"]
        new_state = None

        if args == "on":
            new_state = True
        elif args == "off":
            new_state = False
        elif not args:
            # Show current status
            status_text = self.strings("triggers_status").format(status=self.strings("triggers_status_on") if current_state else self.strings("triggers_status_off"))
            await utils.answer(message, status_text)
            if message.out:
                await message.delete()
            return
        else:
            await utils.answer(message, self.strings("triggers_invalid_arg"))
            if message.out:
                await message.delete()
            return

        if new_state is not None:
            if current_state == new_state:
                status_text = self.strings("triggers_already_in_state").format(
                    state=self.strings("triggers_status_on") if new_state else self.strings("triggers_status_off")
                )
                await utils.answer(message, status_text)
            else:
                self.config["triggers_enabled"] = new_state
                status_text = self.strings("triggers_state_changed").format(
                    new_state=self.strings("triggers_status_on") if new_state else self.strings("triggers_status_off")
                )
                await utils.answer(message, status_text)
            if message.out:
                await message.delete()
