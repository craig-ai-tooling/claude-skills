.PHONY: init build upload upload-all sync sync-project sync-private validate clean list list-remote flatten help delete

SKILL ?=
SKILLS_DIR := skills
PRIVATE_DIR := private-skills
SCRIPTS_DIR := scripts
DIST_DIR := dist

# Resolve SKILL=name across both trees (public first). Empty if not found —
# targets that need an existing skill check this; init doesn't (skill is new).
SKILL_PATH := $(firstword $(wildcard $(SKILLS_DIR)/$(SKILL) $(PRIVATE_DIR)/$(SKILL)))

define require_skill_path
	@test -n "$(SKILL_PATH)" || { echo "Error: skill '$(SKILL)' not found in $(SKILLS_DIR)/ or $(PRIVATE_DIR)/"; exit 1; }
endef

help:
	@echo "Skills Management (covers skills/ AND private-skills/ unless noted)"
	@echo ""
	@echo "  make init SKILL=name      Create new skill from template"
	@echo "  make init SKILL=name PRIVATE=1   ...in private-skills/ instead"
	@echo "  make build                Package all skills (public + private)"
	@echo "  make build SKILL=name     Package specific skill"
	@echo "  make upload SKILL=name    Upload specific skill to API (private allowed, explicit only)"
	@echo "  make upload-all           Upload all PUBLIC skills to API (private never bulk-uploaded)"
	@echo "  make sync                 Symlink all skills (public + private) to ~/.claude/skills"
	@echo "  make sync-project         Symlink all skills (public + private) to .claude/skills"
	@echo "  make sync-private         Symlink only private-skills/ to ~/.claude/skills"
	@echo "  make validate             Validate all skills + secret-scan skills/ (public only)"
	@echo "  make validate SKILL=name  Validate specific skill"
	@echo "  make flatten              Flatten all skills to dist/flattened/"
	@echo "  make flatten SKILL=name   Flatten specific skill"
	@echo "  make list                 List all local skills"
	@echo "  make list-remote          List skills on Anthropic API"
	@echo "  make clean                Remove dist/"
	@echo ""
	@echo "Environment variables:"
	@echo "  ANTHROPIC_API_KEY         Required for upload commands"

init:
ifndef SKILL
	$(error SKILL is required. Usage: make init SKILL=my-skill-name [PRIVATE=1])
endif
ifdef PRIVATE
	@python3 $(SCRIPTS_DIR)/init_skill.py --base-dir $(PRIVATE_DIR) $(SKILL)
else
	@python3 $(SCRIPTS_DIR)/init_skill.py $(SKILL)
endif

build:
ifdef SKILL
	$(require_skill_path)
	@python3 $(SCRIPTS_DIR)/package_skill.py $(SKILL_PATH)
else
	@python3 $(SCRIPTS_DIR)/package_skill.py $(wildcard $(SKILLS_DIR)/*/) $(wildcard $(PRIVATE_DIR)/*/)
endif

upload:
ifndef SKILL
	$(error SKILL is required. Usage: make upload SKILL=my-skill-name)
endif
	$(require_skill_path)
	@python3 $(SCRIPTS_DIR)/upload_skill.py $(SKILL_PATH)

# Deliberately public-only: private-skills/ contains lab identifiers and is
# never bulk-uploaded. Upload a private skill only via explicit
# `make upload SKILL=name`.
upload-all:
	@python3 $(SCRIPTS_DIR)/upload_skill.py --all

sync: sync-private
	@bash $(SCRIPTS_DIR)/sync_local.sh

sync-project:
	@bash $(SCRIPTS_DIR)/sync_local.sh --project
	@mkdir -p .claude/skills
	@for skill_dir in $(PRIVATE_DIR)/*/; do \
		if [ -f "$$skill_dir/SKILL.md" ]; then \
			name=$$(basename "$$skill_dir"); \
			ln -sfn "$(CURDIR)/$(PRIVATE_DIR)/$$name" ".claude/skills/$$name"; \
			echo "  linked (private): $$name"; \
		fi \
	done

# private-skills/ sits OUTSIDE skills/ on purpose: deploy.yml's path filter
# (skills/**) never uploads it. Symlinking is its primary distribution.
sync-private:
	@mkdir -p $(HOME)/.claude/skills
	@for skill_dir in $(PRIVATE_DIR)/*/; do \
		if [ -f "$$skill_dir/SKILL.md" ]; then \
			name=$$(basename "$$skill_dir"); \
			ln -sfn "$(CURDIR)/$(PRIVATE_DIR)/$$name" "$(HOME)/.claude/skills/$$name"; \
			echo "  linked (private): $$name"; \
		fi \
	done

# Secret scan covers skills/ only: private-skills/ legitimately contains lab
# identifiers (that's what makes it private).
validate:
ifdef SKILL
	$(require_skill_path)
	@python3 $(SCRIPTS_DIR)/quick_validate.py $(SKILL_PATH)
else
	@for skill_dir in $(SKILLS_DIR)/*/ $(PRIVATE_DIR)/*/; do \
		if [ -f "$$skill_dir/SKILL.md" ]; then \
			python3 $(SCRIPTS_DIR)/quick_validate.py "$$skill_dir"; \
		fi \
	done
	@python3 $(SCRIPTS_DIR)/secret_scan.py $(SKILLS_DIR)
	python3 $(SCRIPTS_DIR)/check_doc_skills.py
endif

list:
	@echo "Local skills:"
	@echo ""
	@for skill_dir in $(SKILLS_DIR)/*/; do \
		if [ -f "$$skill_dir/SKILL.md" ]; then \
			echo "  $$(basename "$$skill_dir")"; \
		fi \
	done
	@for skill_dir in $(PRIVATE_DIR)/*/; do \
		if [ -f "$$skill_dir/SKILL.md" ]; then \
			echo "  $$(basename "$$skill_dir") (private)"; \
		fi \
	done
	@echo ""

list-remote:
	@python3 $(SCRIPTS_DIR)/upload_skill.py --list

flatten:
ifdef SKILL
	$(require_skill_path)
	@python3 $(SCRIPTS_DIR)/flatten_skill.py $(SKILL_PATH)
else
	@python3 $(SCRIPTS_DIR)/flatten_skill.py --all
	@for skill_dir in $(PRIVATE_DIR)/*/; do \
		if [ -f "$$skill_dir/SKILL.md" ]; then \
			python3 $(SCRIPTS_DIR)/flatten_skill.py "$$skill_dir"; \
		fi \
	done
endif

clean:
	@rm -rf $(DIST_DIR)
	@echo "Cleaned $(DIST_DIR)/"

delete:
ifndef ID
	$(error ID is required. Usage: make delete ID=skill_01abc123)
endif
	@python3 $(SCRIPTS_DIR)/upload_skill.py --delete $(ID)
