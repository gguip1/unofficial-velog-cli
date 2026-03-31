# PostFlow

Markdown으로 블로그 글을 관리하고 Velog에 발행하는 CLI 도구.

## 명령어

| 명령어 | 설명 |
|--------|------|
| `postflow init` | 프로젝트 초기화. Velog username 입력 → `config/postflow.yaml` 생성 |
| `postflow login` | Velog 로그인. 브라우저에서 쿠키 토큰을 복사해 입력 |
| `postflow logout` | 저장된 인증 세션 삭제 (`~/.postflow/`) |
| `postflow sync` | Velog 글을 로컬로 동기화. 이미지 다운로드 포함 |
| `postflow create` | 새 글 생성. `posts/<slug>/content.md` + `meta.yaml` |
| `postflow list` | 글 목록 출력. `--status draft` 등 필터 가능 |
| `postflow check` | 메타데이터/구조 검증. `postflow check <slug>`로 단일 글 검증 가능 |
| `postflow publish` | Velog에 발행. 인자 없으면 변경된 글 다중 선택, `--slug`로 특정 글 지정 |
| `postflow doctor` | 환경 점검 (Python, 설정, 인증 상태 등) |

## 프로젝트 구조

```
PostFlow/
├── config/postflow.yaml      # 사용자 설정 (init으로 생성, gitignore됨)
├── posts/
│   ├── registry.yaml          # 글 상태 인덱스
│   └── <slug>/
│       ├── content.md         # 글 본문
│       ├── meta.yaml          # 메타데이터
│       └── images/            # 이미지 + mapping.json
├── src/postflow/
│   ├── commands/              # CLI 명령어
│   ├── core/                  # 비즈니스 로직
│   ├── adapters/velog/        # Velog GraphQL API 클라이언트
│   └── models/                # Pydantic 데이터 모델
└── templates/                 # 글 생성 시 사용하는 템플릿
```

## 글 작성 흐름

1. `postflow create` → 제목/슬러그 입력 → `posts/<slug>/` 생성
2. `posts/<slug>/content.md` 편집
3. `postflow publish` → 변경된 글 선택 → Velog에 발행

## 주의사항

- Velog 비공식 GraphQL API(v3.velog.io/graphql) 사용
- 인증 토큰은 `~/.postflow/velog-auth.json`에 저장됨 (프로젝트 외부)
- `config/postflow.yaml`은 `.gitignore`에 포함됨
- 발행 시 로컬 이미지 경로(`./images/...`)는 자동으로 원본 URL로 복원됨
