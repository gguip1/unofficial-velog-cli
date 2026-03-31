# PostFlow

Markdown으로 블로그 글을 쓰고, CLI로 Velog에 발행하는 도구입니다.

글은 Git 저장소에서 관리하고, 발행/동기화는 명령어 하나로 처리합니다.

## 시작하기

### 1. 저장소 만들기

GitHub에서 "Use this template"을 클릭하여 내 저장소를 만드세요.

### 2. 설치

```bash
git clone https://github.com/<username>/PostFlow.git
cd PostFlow
python -m venv .venv
```

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

```bash
pip install -e .
```

### 3. 초기화

```bash
postflow init
```

Velog 사용자명을 입력하면 설정 파일(`config/postflow.yaml`)이 생성됩니다.

### 4. Velog 로그인

```bash
postflow login
```

브라우저에서 Velog에 로그인한 후, 개발자 도구(F12)에서 쿠키의 `access_token`과 `refresh_token`을 복사해 입력합니다. 토큰은 30일간 유효합니다.

## 사용법

### 기존 Velog 글 가져오기

```bash
postflow sync
```

Velog에 있는 글을 이미지와 함께 로컬로 가져옵니다. 이미 가져온 글은 업데이트하고, Velog에서 삭제된 글은 알려줍니다.

### 새 글 만들기

```bash
postflow create
```

제목과 슬러그를 입력하면 `posts/<slug>/` 디렉토리에 `content.md`와 `meta.yaml`이 생성됩니다.

### 글 발행하기

```bash
postflow publish
```

변경된 글 목록이 표시되고, 발행할 글을 선택할 수 있습니다. 특정 글만 발행하려면:

```bash
postflow publish --slug my-post
```

### 글 목록 보기

```bash
postflow list
postflow list --status draft
```

### 글 검증하기

```bash
postflow check
postflow check my-post
```

### 환경 점검

```bash
postflow doctor
```

Python 버전, 설정 파일, Velog 인증 상태 등을 점검합니다.

### 로그아웃

```bash
postflow logout
```

저장된 인증 정보를 삭제합니다.

## 글 구조

```
posts/
  my-post/
    content.md          # 글 본문 (Markdown)
    meta.yaml           # 메타데이터 (제목, 태그, 공개 여부 등)
    images/             # 이미지 (sync 시 자동 다운로드)
      image-1-abc123.png
      mapping.json      # 로컬 경로 <-> 원본 URL 매핑
```

### meta.yaml 예시

```yaml
id: V1StGXR8_Z5jdHi6B-myT
title: 내 글 제목
slug: my-post
description: 글 요약
tags:
  - Python
  - CLI
status: draft          # draft / ready / published
visibility: public     # public / private
series: null           # Velog 시리즈명 (선택)
```

## 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `postflow init` | 프로젝트 초기화 |
| `postflow login` | Velog 로그인 |
| `postflow logout` | 로그인 세션 삭제 |
| `postflow sync` | Velog 글 동기화 (가져오기/업데이트) |
| `postflow create` | 새 글 생성 |
| `postflow list` | 글 목록 출력 |
| `postflow check` | 메타데이터/구조 검증 |
| `postflow publish` | Velog에 발행 |
| `postflow doctor` | 환경 점검 |

## 주의사항

- Velog GraphQL API는 비공식입니다. API가 변경되면 동작하지 않을 수 있습니다.
- 로컬을 원본으로 사용합니다. Velog에서 직접 수정 후 sync 없이 publish하면 Velog 수정분이 덮어써집니다.
- 인증 토큰은 `~/.postflow/`에 저장되며 Git에 포함되지 않습니다.
