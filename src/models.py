from sqlalchemy import (Boolean, CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint,)
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TournamentInfo(Base):
    __tablename__ = "tournament_info"

    season_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    season: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )
    champion: Mapped[str | None] = mapped_column(String(200))
    mvp_candidates: Mapped[str | None] = mapped_column(String(1000))


class TeamInfo(Base):
    __tablename__ = "team_info"

    team_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    team_name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True
    )
    founded_year: Mapped[int | None] = mapped_column(Integer)



class PlayerInfo(Base):
    __tablename__ = "player_info"

    player_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    birth_date: Mapped[str | None] = mapped_column(
        String(20)
    )
    height: Mapped[float | None] = mapped_column(
        Float
    )
    weight: Mapped[float | None] = mapped_column(
        Float
    )
    experience: Mapped[int | None] = mapped_column(
        Integer
    )



class PositionInfo(Base):
    __tablename__ = "position_info"

    position_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    position_name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )


class PlayerStats(Base):
    __tablename__ = "player_stats"

    player_stat_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("player_info.player_id"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("team_info.team_id"), nullable=False
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_info.season_id"), nullable=False
    )
    position_id: Mapped[int] = mapped_column(
        ForeignKey("position_info.position_id"), nullable=False
    )

    games_played: Mapped[int | None] = mapped_column(Integer)
    minutes_played: Mapped[float | None] = mapped_column(Float)

    field_goals: Mapped[int | None] = mapped_column(Integer)
    field_goal_attempts: Mapped[int | None] = mapped_column(Integer)

    three_point_field_goals: Mapped[int | None] = mapped_column(Integer)
    three_point_attempts: Mapped[int | None] = mapped_column(Integer)

    two_point_field_goals: Mapped[int | None] = mapped_column(Integer)
    two_point_attempts: Mapped[int | None] = mapped_column(Integer)

    effective_field_goal_pct: Mapped[float | None] = mapped_column(Float)

    free_throws: Mapped[int | None] = mapped_column(Integer)
    free_throw_attempts: Mapped[int | None] = mapped_column(Integer)

    total_rebounds: Mapped[int | None] = mapped_column(Integer)
    personal_fouls: Mapped[int | None] = mapped_column(Integer)
    points: Mapped[int | None] = mapped_column(Integer)
    assists: Mapped[float | None] = mapped_column(Float)
    steals: Mapped[float | None] = mapped_column(Float)
    blocks: Mapped[float | None] = mapped_column(Float)
    turnovers: Mapped[float | None] = mapped_column(Float)

    mvp_candidate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "team_id",
            "season_id",
            name="uq_player_team_season",
        ),
        CheckConstraint(
            "games_played IS NULL OR games_played >= 0",
            name="ck_player_games_nonnegative",
        ),
    )


class TeamStats(Base):
    __tablename__ = "team_stats"

    team_stat_id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("team_info.team_id"), nullable=False
    )
    season_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_info.season_id"), nullable=False
    )

    win_loss_pct: Mapped[float | None] = mapped_column(Float)
    simple_rating_system: Mapped[float | None] = mapped_column(Float)
    relative_pace: Mapped[float | None] = mapped_column(Float)
    relative_offensive_rating: Mapped[float | None] = mapped_column(Float)
    relative_defensive_rating: Mapped[float | None] = mapped_column(Float)
    finish: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "season_id",
            name="uq_team_season",
        ),
    )