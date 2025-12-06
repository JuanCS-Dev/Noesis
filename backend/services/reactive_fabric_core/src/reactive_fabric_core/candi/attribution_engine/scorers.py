"""
Scoring Functions for Attribution Engine.

TTP, tool, infrastructure, and sophistication scoring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from ..forensic_analyzer import ForensicReport
    from ..threat_intelligence import ThreatIntelReport


class AttributionScorerMixin:
    """Mixin providing scoring capabilities for attribution."""

    threat_actors: Dict[str, Dict[str, Any]]
    ttp_signatures: Dict[str, Dict[str, Any]]
    tool_signatures: Dict[str, Dict[str, Any]]
    infrastructure_db: Dict[str, Dict[str, Any]]

    def _score_ttp_overlap(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport
    ) -> Dict[str, float]:
        """Score TTP overlap with known actors."""
        scores = {}

        observed_behaviors = set(forensic.behaviors)

        for actor, signature in self.ttp_signatures.items():
            known_ttps = set(signature['ttps'])

            if not known_ttps:
                continue

            intersection = observed_behaviors & known_ttps
            union = observed_behaviors | known_ttps

            if union:
                similarity = len(intersection) / len(union)
                scores[actor] = similarity * 100.0

        return scores

    def _score_tool_usage(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport
    ) -> Dict[str, float]:
        """Score tool usage matching."""
        scores = {}

        observed_tools = set()
        if forensic.malware_family:
            observed_tools.add(forensic.malware_family.lower())

        for tool in intel.known_tools:
            observed_tools.add(tool.lower())

        if not observed_tools:
            return scores

        for actor, signature in self.tool_signatures.items():
            known_tools = set(t.lower() for t in signature['tools'])

            if not known_tools:
                continue

            matches = observed_tools & known_tools

            if matches:
                score = (len(matches) / len(known_tools)) * 100.0
                scores[actor] = min(score, 100.0)

        return scores

    def _score_infrastructure(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport
    ) -> Dict[str, float]:
        """Score infrastructure matching."""
        scores = {}

        source_ip = forensic.source_ip

        if not source_ip or source_ip == 'unknown':
            return scores

        for actor, infra in self.infrastructure_db.items():
            for ip_range in infra.get('ip_ranges', []):
                if self._ip_in_range(source_ip, ip_range):
                    scores[actor] = scores.get(actor, 0.0) + 50.0

        return scores

    def _score_sophistication(self, forensic: ForensicReport) -> Dict[str, float]:
        """Score sophistication level matching."""
        scores = {}

        sophistication = forensic.sophistication_score

        for actor, profile in self.threat_actors.items():
            expected_sophistication = profile.get('typical_sophistication', 5.0)
            diff = abs(sophistication - expected_sophistication)
            score = max(0, 100 - (diff * 10))
            scores[actor] = score

        return scores

    def _aggregate_scores(
        self,
        ttp_scores: Dict[str, float],
        tool_scores: Dict[str, float],
        infra_scores: Dict[str, float],
        sophistication_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Aggregate scores with weighted average."""
        weights = {
            'ttp': 0.40,
            'tool': 0.25,
            'infra': 0.20,
            'sophistication': 0.15
        }

        all_actors = set()
        all_actors.update(ttp_scores.keys())
        all_actors.update(tool_scores.keys())
        all_actors.update(infra_scores.keys())
        all_actors.update(sophistication_scores.keys())

        final_scores = {}

        for actor in all_actors:
            score = 0.0
            score += ttp_scores.get(actor, 0.0) * weights['ttp']
            score += tool_scores.get(actor, 0.0) * weights['tool']
            score += infra_scores.get(actor, 0.0) * weights['infra']
            score += sophistication_scores.get(actor, 0.0) * weights['sophistication']
            final_scores[actor] = score

        return final_scores

    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in range (simplified)."""
        if '/' in ip_range:
            prefix = ip_range.split('/')[0].rsplit('.', 1)[0]
            return ip.startswith(prefix)
        return ip == ip_range

    def _get_matching_ttps(self, actor: str, forensic: ForensicReport) -> List[str]:
        """Get TTPs that match the attributed actor."""
        matches = []

        if actor in self.ttp_signatures:
            known_ttps = set(self.ttp_signatures[actor]['ttps'])
            observed = set(forensic.behaviors)
            matches = list(known_ttps & observed)

        return matches

    def _get_matching_tools(
        self,
        actor: str,
        forensic: ForensicReport,
        intel: ThreatIntelReport
    ) -> List[str]:
        """Get tools that match the attributed actor."""
        matches = []

        if actor in self.tool_signatures:
            known_tools = set(t.lower() for t in self.tool_signatures[actor]['tools'])

            if forensic.malware_family and forensic.malware_family.lower() in known_tools:
                matches.append(forensic.malware_family)

            for tool in intel.known_tools:
                if tool.lower() in known_tools:
                    matches.append(tool)

        return matches

    def _get_matching_infrastructure(
        self,
        actor: str,
        forensic: ForensicReport
    ) -> List[str]:
        """Get infrastructure that matches the attributed actor."""
        matches = []

        source_ip = forensic.source_ip

        if actor in self.infrastructure_db and source_ip != 'unknown':
            infra = self.infrastructure_db[actor]

            for ip_range in infra.get('ip_ranges', []):
                if self._ip_in_range(source_ip, ip_range):
                    matches.append(f"IP in known range: {ip_range}")

        return matches

    def _detect_apt_indicators(
        self,
        forensic: ForensicReport,
        intel: ThreatIntelReport,
        actor_profile: Dict[str, Any]
    ) -> List[str]:
        """Detect APT-specific indicators."""
        indicators = []

        if forensic.sophistication_score >= 7:
            indicators.append("High sophistication score")

        if len(set(forensic.attack_stages)) >= 3:
            indicators.append("Multi-stage attack chain")

        if forensic.malware_family and 'custom' in forensic.malware_family.lower():
            indicators.append("Custom malware detected")

        apt_tools = ['mimikatz', 'cobalt strike', 'metasploit', 'empire', 'covenant']
        for tool in intel.known_tools:
            if any(apt_tool in tool.lower() for apt_tool in apt_tools):
                indicators.append(f"APT tool detected: {tool}")

        if actor_profile.get('type') == 'nation_state':
            indicators.append("Attributed to nation-state actor")

        if 'persistence' in forensic.attack_stages:
            indicators.append("Persistence mechanisms deployed")

        if 'lateral_movement' in forensic.behaviors:
            indicators.append("Lateral movement attempted")

        return indicators
