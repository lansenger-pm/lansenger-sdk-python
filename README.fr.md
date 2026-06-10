[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# lansenger-sdk

SDK Python indépendant du framework pour la plateforme Lansenger (蓝信) — prend en charge les applications Lansenger, les bots d'organisation et les bots personnels.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests: 341](https://img.shields.io/badge/Tests-341-green)](https://github.com/lansenger-pm/lansenger-sdk-python)

> 💠 Zéro dépendance de framework — uniquement `httpx`. Fonctionne avec tout codebase Python async ou sync.

## Types de bots pris en charge

| Type de bot | Auth | WebSocket entrant | Toutes les API |
|-------------|------|-------------------|----------------|
| **Application Lansenger** | appToken + userToken | ✗ (utilise webhook) | ✓ |
| **Bot d'organisation** | appToken + userToken | ✗ (utilise webhook) | ✓ |
| **Bot personnel** | appToken | ✓ (WebSocket) | ✓ (limité pour les API non-bot) |

Les trois types de bots utilisent le même mécanisme d'authentification : `appToken` est requis pour chaque appel API ; `userToken` est uniquement nécessaire pour certaines opérations au niveau utilisateur (infos utilisateur, recherche de staff, calendrier, etc.).

## Fonctionnalités

- **Clients async & sync** — `LansengerClient` (async) + `LansengerSyncClient` (bloquant)
- **Persistance des identifiants & tokens** — `CredentialStore` sauvegarde app_id, app_secret, URLs, appToken, userToken dans un fichier (survit aux redémarrages)
- **Authentification utilisateur OAuth2** — URL d'autorisation, échange de code, refresh de token
- **Organisation & départements** — infos org, détail/children/staff de département
- **Staff & contacts** — infos basiques/détaillées, mapping d'ID, ancêtres de département, recherche
- **Messagerie** — 3 canaux de chat privé (bot, compte officiel, impersonnation utilisateur) + chat de groupe, tous les types de messages, @mention, identité humain/bot, rappels urgents
- **Cartes riches** — appCard (avec mises à jour dynamiques), oacard, linkCard, verifyCard, appArticles
- **Messages en streaming** — delivery en temps réel basé sur SSE pour les agents IA
- **Upload/download de médias** — fichiers, images, vidéos avec detection automatique du type, récupération du chemin média
- **Gestion des messages** — révocation, mise à jour dynamique de carte
- **Groups** — créer, infos, membres, liste, vérification de membership, mise à jour des paramètres & membres, dissoudre
- **Calendrier & Schedule** — calendrier principal, CRUD de schedule + mise à jour, gestion des participants + métadonnées participants
- **Todo unifié** — créer, mettre à jour, supprimer, interroger, gestion d'exécuteur, comptes de statut
- **Événements de callback** — 25 types d'événements, parsing structuré, décryptage AES (spec 4.10.1.4), vérification de signature SHA1

## Installation rapide

```bash
pip install lansenger-sdk
```

Pour le développement :

```bash
pip install -e ".[dev]"
```

## 1. Authentification

### appToken — Requis pour tous les appels API

Chaque méthode du SDK requiert `appToken`. Le client l'obtient et le refresh automatiquement à partir de votre `app_id` + `app_secret`. Vous n'avez jamais besoin de gérer appToken manuellement — le `TokenManager` gère le cycle de vie :

1. **Premier appel** → `GET /v1/apptoken/create` avec app_id + app_secret → renvoie `appToken` (valide 2 heures)
2. **Appels suivants** → réutilise le appToken en cache jusqu'à expiration
3. **Token expiré** → refresh automatique via le même endpoint

```python
# appToken est géré automatiquement — configurez juste app_id + app_secret
client = LansengerClient(app_id="your-appid", app_secret="your-secret")

# Vous pouvez aussi obtenir/invalider le token manuellement
token = await client.get_token()
client.invalidate_token()  # force le refresh au prochain appel
```

### userToken — Uniquement nécessaire pour certains endpoints

`userToken` représente l'autorisation d'un utilisateur Lansenger spécifique (obtenu via OAuth2). Il est uniquement requis pour :
- Informations au niveau utilisateur (fetch_user_info, fetch_staff_detail, search_staff)
- Opérations de calendrier & schedule (fetch_primary_calendar, create_schedule, etc.)
- Opérations de groupe comme envoyeur humain

### Obtenir les identifiants

| Type de bot | Comment obtenir app_id + app_secret |
|-------------|--------------------------------------|
| **Bot personnel** | Client Lansenger (desktop) → Contacts → Bots intelligents → Bots personnels → cliquer sur l'icône ℹ️ (le client mobile ne permet pas de voir les identifiants) |
| **Application Lansenger** | Créer sur le [Lansenger Developer Center](https://dev.lanxin.cn) — peut nécessiter l'approbation de l'administrateur de l'organisation |
| **Bot d'organisation** | Créer sur le [Lansenger Developer Center](https://dev.lanxin.cn) — peut nécessiter l'approbation de l'administrateur de l'organisation |

### Authentification OAuth2 niveau utilisateur

```python
# Construire l'URL d'autorisation — rediriger l'utilisateur vers Lansenger passport
url = client.build_authorize_url(redirect_uri="https://myapp.com/callback")

# Après autorisation de l'utilisateur, échanger le code pour userToken + refreshToken
token_result = await client.exchange_code(code="auth_code_from_callback")

# Refresh un userToken expiré
new_token = await client.refresh_user_token(refresh_token=token_result.refresh_token)

# Récupérer le profil utilisateur
user_info = await client.fetch_user_info(user_token=token_result.user_token)
```

## 2. Organisation & Départements

```python
# Infos organisation
org = await client.fetch_org_info(org_id="orgId")

# Hiérarchie des départements
detail = await client.fetch_department_detail(department_id="deptId")
children = await client.fetch_department_children(department_id="deptId")
staffs = await client.fetch_department_staffs(department_id="deptId")
```

## 3. Staff & Contacts

```python
# Infos basiques du staff
staff = await client.fetch_staff_basic_info(staff_id="staffOpenId")

# Profil détaillé (userToken recommandé)
detail = await client.fetch_staff_detail(staff_id="staffOpenId", user_token="ut")

# Mapper téléphone → staffId
mapping = await client.fetch_staff_id_mapping(
    org_id="orgId", id_type="mobile", id_value="13800138000"
)

# Ancêtres de département pour un membre du staff
ancestors = await client.fetch_department_ancestors(staff_id="staffOpenId")

# Rechercher du staff (requiert userToken ou userId)
results = await client.search_staff(keyword="Zhang San", user_token="ut")

# IDs de champs extra de l'org
fields = await client.fetch_org_extra_field_ids(org_id="orgId")
```

## 4. Messagerie & Médias

#### Chat privé de bot — le plus courant

```python
result = await client.send_text(chat_id="staff123", content="Hello!")
result = await client.send_markdown(chat_id="staff123", content="**Bold**")
result = await client.send_file(chat_id="staff123", file_path="/path/to/report.pdf")
```

#### Canal compte officiel

```python
result = await client.send_account_message(
    msg_type="text", msg_data={"text": {"content": "System notice"}},
    chat_ids=["staff1", "staff2"], account_id="524288-xxxx",
)
```

#### Canal impersonnation utilisateur (requiert userToken)

```python
result = await client.send_user_message(
    receiver_id="staff456", msg_type="text",
    msg_data={"text": {"content": "Hello"}},
    user_token="ut",  # requis
)
```

#### Chat de groupe

```python
# Bot → groupe
result = await client.send_text(chat_id="group123", content="Notice", is_group=True)

# Humain → groupe (avec userToken)
result = await client.send_group_message(
    group_id="group123", msg_type="text",
    msg_data={"text": {"content": "I'll handle it"}},
    user_token="ut",
)

# Le chat de groupe supporte TOUS les types de messages (text, formatText, oacard, appCard, linkCard, etc.)
result = await client.send_group_message(
    group_id="group123", msg_type="appCard",
    msg_data={"appCard": {"bodyTitle": "Approbation", "isDynamic": True}},
    user_token="ut",
)

# @mention dans un groupe
result = await client.send_text(
    chat_id="group123", content="Important!", is_group=True, reminder_all=True,
)
```

#### Cartes enrichies

```python
result = await client.send_app_card(chat_id="staff123", body_title="Approbation", is_dynamic=True)
result = await client.send_link_card(chat_id="staff123", title="Article", link="https://...")
result = await client.send_app_articles(chat_id="staff123", articles=[...])

# Mettre à jour le statut d'une carte dynamique
result = await client.update_dynamic_card(msg_id="msg123", is_last_update=True)
```

#### Messages en streaming (pour agents IA)

```python
result = await client.create_stream_message(receiver_id="staff1", receiver_type="staff", stream_id="s1")
result = await client.fetch_stream_message(msg_id="msg123")
```

#### Médias

```python
# Upload
upload = await client.upload_media(file_path="/path/to/file.pdf")

# Download
download = await client.download_media(media_id="media123")

# Récupérer le chemin de téléchargement (4.5.3)
path_result = await client.fetch_media_path(media_id="media123")

# Révoquer des messages
result = await client.revoke_message(message_ids=["msg1", "msg2"])
```

#### Rappels urgents (4.6.14)

```python
from lansenger_sdk import REMINDER_TYPE_POPUP, REMINDER_TYPE_SMS, REMINDER_TYPE_PHONE

result = await client.send_reminder(
    msg_id="msg123",
    reminder_types=[REMINDER_TYPE_POPUP, REMINDER_TYPE_SMS],
    user_id_list=["staff1", "staff2"],
)
```

## 5. Groups

```python
# Créer un groupe
group = await client.create_group(name="Chat Projet", org_id="orgId", staff_id_list=["s1","s2","s3"])

# Récupérer infos & membres
info = await client.fetch_group_info(group_id="groupOpenId")
members = await client.fetch_group_members(group_id="groupOpenId")
groups = await client.fetch_group_list()

# Vérifier le membership
result = await client.check_is_in_group(group_id="groupOpenId", staff_id="staff1")

# Mettre à jour les paramètres
await client.update_group_info(group_id="groupId", name="Nouveau nom", manage_mode=1)

# Ajouter/supprimer des membres
await client.update_group_members(
    group_id="groupId", add_user_list=["staff4"], del_user_list=["staff3"],
)

# Dissoudre un groupe (propriétaire uniquement, 4.28.6)
await client.dismiss_group(group_id="groupId")
```

## 6. Calendrier & Schedule

```python
# Récupérer le calendrier principal (requiert userToken ou userId)
cal = await client.fetch_primary_calendar(user_token="ut")

# Créer un schedule
schedule = await client.create_schedule(
    calendar_id=cal.calendar_id, summary="Réunion d'équipe",
    start_time={"date": "2024-01-15", "time": "10:00", "timeZone": "Asia/Shanghai"},
    end_time={"date": "2024-01-15", "time": "11:00", "timeZone": "Asia/Shanghai"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
    user_token="ut",
)

# Récupérer/supprimer un schedule
info = await client.fetch_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.delete_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")

# Liste de schedules dans un intervalle de temps (max 42 jours)
schedules = await client.fetch_schedule_list(
    calendar_id="cal1", start_time=1705276800000, end_time=1707940800000, user_token="ut",
)

# Gestion des participants
attendees = await client.fetch_schedule_attendees(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.add_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
await client.delete_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")

# Mettre à jour un schedule (4.23.12)
await client.update_schedule(
    calendar_id="cal1", schedule_id="sch1",
    summary="Réunion mise à jour", operation_type="modify_all",
    user_token="ut",
)

# Mettre à jour les métadonnées de participant (4.23.17) — RSVP, couleur, occupé/libre, rappels
await client.update_schedule_attendee_meta(
    calendar_id="cal1", schedule_id="sch1",
    rsvp_status="accept", busy_free_state="busy",
    remind_times=[5, 15], user_token="ut",
)
```

## 7. Todo unifié

```python
from lansenger_sdk import TODO_TYPE_APPROVAL, TODO_TODO_STATUS_DONE

# Créer une tâche todo
todo = await client.create_todo_task(
    title="Demande d'approbation", link="https://app.com/a/1", pc_link="https://pc.app.com/a/1",
    executor_ids=["staff1"], org_id="org1", type=TODO_TYPE_APPROVAL,
)

# Mettre à jour le statut (11=à lire, 12=lu, 21=à faire, 22=fait)
await client.update_todo_task_status(todotask_id="taskId", status=TODO_TODO_STATUS_DONE, org_id="org1")

# Mettre à jour le contenu
await client.update_todo_task(todotask_id="taskId", title="Mis à jour", link="l", pc_link="p", org_id="org1")

# Supprimer (envoyeur uniquement)
await client.delete_todo_task(todotask_id="taskId", org_id="org1")

# Interroger
list_result = await client.fetch_todo_task_list(org_id="org1")
task = await client.fetch_todo_task_by_id(todotask_id="taskId", org_id="org1")
task = await client.fetch_todo_task_by_source_id(source_id="src1", org_id="org1")
counts = await client.fetch_todo_task_status_counts(staff_id="staff1", org_id="org1")

# Gestion des exécuteurs
await client.add_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
await client.delete_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
executors = await client.fetch_executor_list(todotask_id="taskId", org_id="org1")
await client.update_executor_status(
    executor_status_list=[{"executorId": "staff1", "todotaskId": "taskId", "status": "22"}],
    org_id="org1",
)
```

## 8. Événements de callback

Le SDK prend en charge les payloads de callback en JSON brut et en AES chiffré (selon la spec API Lansenger 4.10.1.4).

### Configuration

Définissez `encoding_key` et `callback_token` (des paramètres de callback du Lansenger Developer Center) :

```python
client = LansengerClient(
    app_id="your-appid", app_secret="your-secret",
    encoding_key="BASE64_AES_KEY",
    callback_token="CALLBACK_TOKEN",
)
```

Ou via les variables d'environnement : `LANSENGER_ENCODING_KEY`, `LANSENGER_CALLBACK_TOKEN`.

### Parser le payload de callback (auto-détecte chiffré vs JSON brut)

```python
from lansenger_sdk import parse_callback_payload, decrypt_callback_payload

# Webhook JSON brut
events = parse_callback_payload('{"events": [...]}')

# Payload chiffré AES (auto-décryptage avec encoding_key)
events = parse_callback_payload(
    encrypted_data,
    encoding_key="BASE64_AES_KEY",
    known_app_id="your-appid",  # aide à séparer orgId/appId dans le buffer décrypté
)
```

### Vérifier la signature

```python
from lansenger_sdk import verify_callback_signature

# sha1(sort(token, timestamp, nonce, dataEncrypt))
is_valid = verify_callback_signature(
    timestamp, nonce, signature, encoding_key,
    data_encrypt=encrypted_data,
    callback_token="CALLBACK_TOKEN",  # revient à encoding_key si vide
)
```

### Décryptage direct

```python
result = decrypt_callback_payload(encrypted_data, encoding_key="KEY", known_app_id="APPID")
# result = {"orgId": "...", "appId": "...", "events": [...], "length": N}
```

### Types d'événements

```python
types = client.get_callback_event_types()  # 25 types d'événements sur 13 catégories
```

Le décryptage AES nécessite le package `pycryptodome` ou `cryptography` (auto-détecté).

## Matrice de capacités des types de messages

| msgType | Markdown | @mention | Attachments | Canaux privés | Chat de groupe | Notes |
|---------|----------|----------|-------------|----------------|----------------|-------|
| `text` | ✗ | ✓ (groupe) | ✓ | Bot, Compte officiel, Impersonnation | ✓ | Max 6000 octets |
| `formatText` | ✓ | ✗ | ✗ | Impersonnation uniquement | ✓ | Markdown (formatType=1) |
| `oacard` | ✗ | ✗ | ✗ | Bot, Compte officiel, Impersonnation | ✓ | Carte simple avec champs |
| `appCard` | ✓ (div) | ✗ | ✗ | Bot, Compte officiel, Impersonnation | ✓ | Carte riche, mises à jour dynamiques |
| `linkCard` | ✗ | ✗ | ✗ | Bot, Compte officiel | ✓ | Carte de lien preview |
| `appArticles` | ✗ | ✗ | ✗ | Bot privé uniquement | ✓ | Liste d'articles (1+ articles) |
| `verifyCard` | ✗ | ✗ | ✗ | Bot, Compte officiel | ✓ | Carte de vérification avec boutons |
| `i18nAppCard` | ✓ (div) | ✗ | ✗ | Bot, Compte officiel, Impersonnation | ✓ | appCard multilingue |
| `i18nSystemAction` | ✗ | ✗ | ✗ | Interne plateforme | ✓ | Action système multilingue |
| `i18nSystem` | ✗ | ✗ | ✗ | Interne plateforme | ✓ | Message système multilingue |

**Chat de groupe** supporte tous les types de messages. Seul le chat de groupe supporte @mention.

## Configuration

### Variables d'environnement

| Variable | Requis | Description | Défaut |
|----------|--------|-------------|--------|
| `LANSENGER_APP_ID` | ✓ | ID App/Bot | — |
| `LANSENGER_APP_SECRET` | ✓ | Secret App/Bot | — |
| `LANSENGER_API_GATEWAY_URL` | ✗ | URL de la passerelle API | `https://open.e.lanxin.cn/open/apigw` |
| `LANSENGER_PASSPORT_URL` | ✗ | URL Passport (pour OAuth2) | — |
| `LANSENGER_REDIRECT_URI` | ✗ | URI de redirection OAuth2 | `http://localhost:8765` |
| `LANSENGER_ENCODING_KEY` | ✗ | Clé de chiffrement AES callback (Base64) | — |
| `LANSENGER_CALLBACK_TOKEN` | ✗ | Token de signature callback | — |

### Persistance des identifiants & tokens

Par défaut, les identifiants et tokens restent en mémoire uniquement (perdus à la sortie du processus). Activez la persistance fichier avec `store_path` :

```python
from lansenger_sdk import LansengerClient, CredentialStore

# Persistance auto vers ~/.lansenger/sdk_state.json (permissions 0600)
client = LansengerClient(
    app_id="...", app_secret="...",
    encoding_key="BASE64_AES_KEY", callback_token="CALLBACK_TOKEN",
    store_path="~/.lansenger/sdk_state.json",
)

# Ou depuis les variables d'environnement avec persistance
client = LansengerClient.from_env(store_path="~/.lansenger/sdk_state.json")

# Opérations manuelles sur le store
store = CredentialStore(path="~/.lansenger/sdk_state.json")
store.save_credentials("app_id", "app_secret", api_gateway_url="...", passport_url="...")
store.save_user_token("user_token", refresh_token="refresh_token")
token = store.load_app_token()  # None si expiré
```

Avec la persistance activée :
- **appToken** est sauvegardé après chaque fetch et restauré au redémarrage (évite les appels API redondants)
- **userToken + refreshToken** sont sauvegardés après l'échange OAuth2
- **Identifiants + URLs** sont sauvegardés ensemble pour une récupération complète

Toutes les méthodes sont disponibles sur `LansengerSyncClient` avec des signatures identiques (bloquant) :

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.send_text(chat_id="staff123", content="Hello!")
org = client.fetch_org_info(org_id="orgId")
```

## Structure du projet

```
lansenger-sdk-python/
├── src/lansenger_sdk/
│   ├── __init__.py          # Toutes les exports
│   ├── client.py            # LansengerClient (async)
│   ├── sync_client.py       # LansengerSyncClient (sync)
│   ├── config.py            # LansengerConfig
│   ├── auth.py              # TokenManager — cycle de vie appToken
│   ├── oauth.py             # Aides OAuth2
│   ├── constants.py         # Endpoints API, types de médias, scopes OAuth
│   ├── exceptions.py        # Hiérarchie LansengerError
│   ├── models.py            # 38+ types de résultat dataclass
│   ├── contacts.py          # API Staff & infos org
│   ├── departments.py       # API Départements
│   ├── account_messages.py  # Canal compte officiel
│   ├── user_messages.py     # Canal impersonnation utilisateur
│   ├── group_messages.py    # Canal Chat de groupe
│   ├── media.py             # Upload/download
│   ├── streaming.py         # Streaming SSE
│   ├── persistence.py       # CredentialStore — persistance fichier des identifiants & tokens
│   ├── callbacks.py         # Événements de callback — 25 types d'événements, parsing structuré, décryptage AES (4.10.1.4), vérification de signature SHA1
│   ├── groups.py            # API Groups (incluant dissoudre 4.28.6)
│   ├── todos.py             # Todo unifié
│   ├── calendars.py         # Calendrier & Schedule (incluant mise à jour 4.23.12, métadonnées participants 4.23.17)
│   ├── reminders.py         # Rappels urgents de messages (4.6.14)
│   └── users.py             # Infos utilisateur
├── tests/                   # 341 tests, tous passants
├── pyproject.toml
└── README*.md               # READMEs en 5 langues
```

## Développement

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Licence

MIT — voir [LICENSE](LICENSE).