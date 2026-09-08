# Dota Drafter - Local Development Commands

.PHONY: help collect validate retrain status rollback

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

collect:  ## Collect matches from OpenDota API
	cd fetch && python fetch.py --target 50000 --output ../data/matches.csv

validate:  ## Validate collected data
	cd fetch && python validator.py ../data/matches.csv

retrain:  ## Force retrain the model
	cd fetch && python scheduler.py --retrain

status:  ## Show pipeline status
	cd fetch && python scheduler.py --status

rollback:  ## Rollback to previous model version
	cd fetch && python scheduler.py --rollback

check-patch:  ## Check for Dota 2 patch updates
	cd fetch && python scheduler.py --check-patch

pipeline:  ## Run full pipeline (check + collect + validate + retrain if needed)
	cd fetch && python scheduler.py --target 50000
