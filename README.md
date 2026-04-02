# unofficial-velog-cli

Markdown으로 Velog 글을 관리하고 발행하는 CLI 도구입니다.

## 시작하기

### 1. 저장소 포크

GitHub에서 unofficial-velog-cli 저장소를 Fork하세요.

### 2. 설치

```bash
git clone https://github.com/<username>/unofficial-velog-cli.git
cd unofficial-velog-cli
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
vcli init
```

Velog 사용자명을 입력하면 설정 파일(`config/vcli.yaml`)이 생성됩니다.

### 4. Velog 로그인

```bash
vcli login
```

브라우저에서 Velog에 로그인한 후, 개발자 도구(F12)에서 쿠키의 `access_token`과 `refresh_token`을 복사해 입력합니다. 토큰은 30일간 유효합니다.

## 사용법

### 기존 Velog 글 가져오기

```bash
vcli sync
```

Velog에 있는 글을 이미지와 함께 로컬로 가져옵니다. 이미 가져온 글은 업데이트하고, Velog에서 삭제된 글은 알려줍니다.

### 새 글 만들기

```bash
vcli create
```

제목과 슬러그를 입력하면 `posts/<slug>/` 디렉토리에 `content.md`와 `meta.yaml`이 생성됩니다.

### 글 발행하기

```bash
vcli publish
```

변경된 글 목록이 표시되고, 발행할 글을 선택할 수 있습니다. 특정 글만 발행하려면:

```bash
vcli publish --slug my-post
```

글에 포함된 로컬 이미지(`./images/...`)는 발행 시 자동으로 Velog에 업로드됩니다.

### 글 목록 보기

```bash
vcli list
vcli list --status draft
```

### 글 검증하기

```bash
vcli check
vcli check my-post
```

### 환경 점검

```bash
vcli doctor
```

Python 버전, 설정 파일, Velog 인증 상태 등을 점검합니다.

### 로그아웃

```bash
vcli logout
```

저장된 인증 정보를 삭제합니다.

## 글 구조

```
posts/
  my-post/
    content.md          # 글 본문 (Markdown)
    meta.yaml           # 메타데이터 (제목, 태그, 공개 여부 등)
    images/             # 이미지 (sync 시 자동 다운로드, publish 시 자동 업로드)
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
| `vcli init` | 프로젝트 초기화 |
| `vcli login` | Velog 로그인 |
| `vcli logout` | 로그인 세션 삭제 |
| `vcli sync` | Velog 글 동기화 (가져오기/업데이트) |
| `vcli create` | 새 글 생성 |
| `vcli list` | 글 목록 출력 |
| `vcli check` | 메타데이터/구조 검증 |
| `vcli publish` | Velog에 발행 |
| `vcli doctor` | 환경 점검 |

## 주의사항

- Velog의 비공식 GraphQL API를 사용합니다. API가 변경되면 동작하지 않을 수 있습니다.
- 로컬을 원본으로 사용합니다. Velog에서 직접 수정 후 sync 없이 publish하면 Velog 수정분이 덮어써집니다.
- 인증 토큰은 `~/.vcli/`에 저장되며 Git에 포함되지 않습니다.
