from typing import List, Dict, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from json_db import json_db

logger = logging.getLogger(__name__)


@dataclass
class AnonymizedHackathonMetrics:
    theme: str
    prize_total: float
    prize_allocation: Dict[str, float]
    duration_days: int
    submission_count: int
    participant_count: int
    challenge_count: int
    judge_count: int
    completion_rate: float
    avg_prize_per_submission: float
    created_at: datetime


class LearningPipeline:
    def __init__(self):
        self.last_aggregation_date: Optional[datetime] = None
    
    def aggregate_hackathon_metrics(self, days_back: int = 7) -> List[AnonymizedHackathonMetrics]:
        try:
            logger.info(f"Aggregating hackathon metrics from last {days_back} days")
            completed_hackathons = json_db.get_completed_hackathons(days_back=days_back)
            metrics = []
            
            for hackathon in completed_hackathons:
                try:
                    theme = hackathon.get("theme", "Unknown")
                    prizes = hackathon.get("prizes", {})
                    
                    prize_total = 0.0
                    if isinstance(prizes.get("total"), str):
                        prize_total = float(prizes["total"].replace("$", "").replace(",", ""))
                    elif isinstance(prizes.get("total"), (int, float)):
                        prize_total = float(prizes["total"])
                    
                    prize_allocation = {"first": 0.5, "second": 0.3, "third": 0.2}
                    if prize_total > 0:
                        first_prize = prizes.get("first", "$0")
                        first_amount = float(str(first_prize).replace("$", "").replace(",", ""))
                        second_prize = prizes.get("second", "$0")
                        second_amount = float(str(second_prize).replace("$", "").replace(",", ""))
                        third_prize = prizes.get("third", "$0")
                        third_amount = float(str(third_prize).replace("$", "").replace(",", ""))
                        
                        if prize_total > 0:
                            prize_allocation = {
                                "first": first_amount / prize_total,
                                "second": second_amount / prize_total,
                                "third": third_amount / prize_total
                            }
                    
                    duration_days = hackathon.get("duration_days", 48)
                    submission_count = hackathon.get("submission_count", hackathon.get("submissions", 0))
                    participant_count = hackathon.get("participant_count", hackathon.get("participants", 0))
                    challenge_count = len(hackathon.get("challenges", []))
                    judge_count = len(hackathon.get("judges", []))
                    
                    completion_rate = submission_count / participant_count if participant_count > 0 else 0.0
                    avg_prize_per_submission = prize_total / submission_count if submission_count > 0 else 0.0
                    
                    metric = AnonymizedHackathonMetrics(
                        theme=theme,
                        prize_total=prize_total,
                        prize_allocation=prize_allocation,
                        duration_days=duration_days,
                        submission_count=submission_count,
                        participant_count=participant_count,
                        challenge_count=challenge_count,
                        judge_count=judge_count,
                        completion_rate=completion_rate,
                        avg_prize_per_submission=avg_prize_per_submission,
                        created_at=datetime.now()
                    )
                    
                    metrics.append(metric)
                    
                except Exception as e:
                    logger.warning(f"Error processing hackathon {hackathon.get('id')}: {e}")
                    continue
            
            logger.info(f"Found {len(metrics)} hackathons to aggregate")
            return metrics
            
        except Exception as e:
            logger.error(f"Error aggregating metrics: {e}")
            return []
    
    def generate_anonymized_summaries(self, metrics: List[AnonymizedHackathonMetrics]) -> List[Dict]:
        summaries = []
        theme_groups: Dict[str, List[AnonymizedHackathonMetrics]] = {}
        for metric in metrics:
            if metric.theme not in theme_groups:
                theme_groups[metric.theme] = []
            theme_groups[metric.theme].append(metric)
        
        for theme, theme_metrics in theme_groups.items():
            if not theme_metrics:
                continue
            
            avg_prize = sum(m.prize_total for m in theme_metrics) / len(theme_metrics)
            avg_duration = sum(m.duration_days for m in theme_metrics) / len(theme_metrics)
            avg_submissions = sum(m.submission_count for m in theme_metrics) / len(theme_metrics)
            avg_completion_rate = sum(m.completion_rate for m in theme_metrics) / len(theme_metrics)
            
            allocation_patterns = {}
            for m in theme_metrics:
                pattern_key = f"{m.prize_allocation['first']:.2f}-{m.prize_allocation['second']:.2f}-{m.prize_allocation['third']:.2f}"
                allocation_patterns[pattern_key] = allocation_patterns.get(pattern_key, 0) + 1
            
            most_common_pattern = max(allocation_patterns.items(), key=lambda x: x[1])[0] if allocation_patterns else None
            
            summary = {
                "theme": theme,
                "sample_size": len(theme_metrics),
                "avg_prize_total": round(avg_prize, 2),
                "avg_duration_days": round(avg_duration, 0),
                "avg_submissions": round(avg_submissions, 0),
                "avg_completion_rate": round(avg_completion_rate, 3),
                "recommended_prize_allocation": most_common_pattern,
                "aggregated_at": datetime.now().isoformat(),
                "type": "theme_summary"
            }
            
            summaries.append(summary)
            
            logger.info(f"Generated summary for {theme}: {summary}")
        
        return summaries
    
    def create_embeddings(self, summaries: List[Dict]) -> List[Dict]:
        embeddings = []
        for summary in summaries:
            allocation_pattern = summary.get("recommended_prize_allocation", "")
            allocation_ratios = None
            if allocation_pattern:
                try:
                    parts = allocation_pattern.split("-")
                    if len(parts) == 3:
                        allocation_ratios = {
                            "first": float(parts[0]),
                            "second": float(parts[1]),
                            "third": float(parts[2])
                        }
                except (ValueError, IndexError):
                    pass
            
            embedding = {
                "id": f"embedding_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(embeddings)}",
                "content": self._summary_to_text(summary),
                "metadata": {
                    "theme": summary.get("theme"),
                    "type": summary.get("type"),
                    "sample_size": summary.get("sample_size"),
                    "aggregated_at": summary.get("aggregated_at"),
                    "prize_allocation_ratios": allocation_ratios,
                    "avg_prize_total": summary.get("avg_prize_total"),
                    "status": "pending_approval"
                },
                "embedding_vector": None
            }
            
            embeddings.append(embedding)
        
        logger.info(f"Created {len(embeddings)} embeddings")
        return embeddings
    
    def _summary_to_text(self, summary: Dict) -> str:
        theme = summary.get("theme", "Unknown")
        sample_size = summary.get("sample_size", 0)
        avg_prize = summary.get("avg_prize_total", 0)
        avg_duration = summary.get("avg_duration_days", 0)
        avg_submissions = summary.get("avg_submissions", 0)
        completion_rate = summary.get("avg_completion_rate", 0)
        
        return (
            f"For {theme} hackathons, based on {sample_size} past events: "
            f"average prize pool ${avg_prize:,.0f}, "
            f"average duration {avg_duration} days, "
            f"average {avg_submissions} submissions with {completion_rate:.1%} completion rate. "
            f"Recommended prize allocation patterns from successful hackathons in this theme."
        )
    
    def store_pending_embeddings(self, embeddings: List[Dict]) -> bool:
        try:
            for embedding in embeddings:
                embedding["metadata"]["status"] = "pending_approval"
                json_db.save_embedding(embedding)
            
            logger.info(f"Stored {len(embeddings)} embeddings in pending queue")
            
            for embedding in embeddings:
                json_db.log_audit_event(
                    event_type="embedding_created",
                    user_id="system",
                    details={
                        "embedding_id": embedding.get("id"),
                        "theme": embedding.get("metadata", {}).get("theme"),
                        "status": "pending_approval"
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error storing pending embeddings: {e}")
            return False
    
    def approve_embeddings(self, embedding_ids: List[str], admin_user_id: str) -> bool:
        try:
            approved_count = 0
            for embedding_id in embedding_ids:
                success = json_db.update_embedding_status(
                    embedding_id=embedding_id,
                    status="approved",
                    admin_user_id=admin_user_id
                )
                
                if success:
                    approved_count += 1
                    json_db.log_audit_event(
                        event_type="embedding_approved",
                        user_id=admin_user_id,
                        details={
                            "embedding_id": embedding_id,
                            "approved_by": admin_user_id
                        }
                    )
                    logger.info(f"Approved embedding {embedding_id}")
            
            logger.info(f"Approved {approved_count} embeddings")
            return approved_count > 0
        except Exception as e:
            logger.error(f"Error approving embeddings: {e}")
            return False
    
    def run_weekly_learning_job(self) -> bool:
        try:
            logger.info("Starting weekly learning job...")
            metrics = self.aggregate_hackathon_metrics(days_back=7)
            
            if not metrics:
                logger.info("No new hackathons to learn from")
                return True
            
            summaries = self.generate_anonymized_summaries(metrics)
            if not summaries:
                logger.warning("No summaries generated")
                return False
            
            embeddings = self.create_embeddings(summaries)
            success = self.store_pending_embeddings(embeddings)
            
            if success:
                self.last_aggregation_date = datetime.now()
                logger.info("Weekly learning job completed successfully")
            
            return success
        except Exception as e:
            logger.error(f"Error in weekly learning job: {e}")
            return False
    
    def get_pending_embeddings(self) -> List[Dict]:
        return json_db.get_pending_embeddings()


learning_pipeline = LearningPipeline()

