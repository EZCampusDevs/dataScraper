from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy import event
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    TIMESTAMP,
    LargeBinary,
    BigInteger,
    VARCHAR,
    ForeignKey,
)
from sqlalchemy import UniqueConstraint
import os

from . import dataUtil
from . import logger

Engine = None
Session = None
Base = declarative_base()


def init_database(database_name: str, database_directory: str):
    global Engine, Session, Base

    if Engine is not None:
        raise Exception("Database engine already initialized")

    os.makedirs(database_directory, exist_ok=True)

    db_path = os.path.join(database_directory, database_name)
    DB_URL = f"sqlite:///{db_path}"
    Engine = create_engine(DB_URL, echo=False)

    def _fk_pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute("pragma foreign_keys=ON")

    event.listen(Engine, "connect", _fk_pragma_on_connect)

    Session = sessionmaker(bind=Engine)
    Base.metadata.bind = Engine
    Base.metadata.create_all(Engine)


class TBL_Terms(Base):
    __tablename__ = "tbl_terms"

    term_id = Column(Integer, primary_key=True)
    term_description = Column(VARCHAR(128))


class TBL_Course(Base):
    __tablename__ = "tbl_course"

    course_id = Column(Integer, primary_key=True, autoincrement=True)
    term_id = Column(Integer, ForeignKey("tbl_terms.term_id"))
    course_code = Column(VARCHAR)
    course_description = Column(VARCHAR)

    __table_args__ = (
        UniqueConstraint("term_id", "course_code", name="_term_id_course_code_constraint"),
    )


class TBL_Class_Type(Base):
    __tablename__ = "tbl_classtype"

    class_type_id = Column(Integer, primary_key=True, autoincrement=True)
    class_type = Column(VARCHAR)


class TBL_Course_Data(Base):
    __tablename__ = "tbl_course_data"

    course_id = Column(Integer, ForeignKey("tbl_course.course_id"), primary_key=True)

    # course reference number / crn
    crn = Column(VARCHAR, primary_key=True)

    # i'm not really sure what this actually is
    id = Column(Integer)

    # Biology II
    course_title = Column(VARCHAR)
    # BIOL
    subject = Column(VARCHAR)
    # Biology
    subject_long = Column(VARCHAR)

    # 001 / 002 / 003...; conerting to int so will need to pad 0 later if needed
    sequence_number = Column(VARCHAR)

    # which campus -> 'OT-North Oshawa'
    campus_description = Column(VARCHAR)

    # lab, lecture, tutorial
    class_type = Column(Integer, ForeignKey("tbl_classtype.class_type_id"))

    credit_hours = Column(Integer)
    maximum_enrollment = Column(Integer)
    enrollment = Column(Integer)
    seats_vailable = Column(Integer)
    wait_capacity = Column(Integer)
    wait_count = Column(Integer)
    wait_available = Column(Integer)
    # cross_list = Column(VARCHAR)
    # cross_list_capacity = Column(VARCHAR)
    # cross_list_count = Column(Integer)
    # cross_list_available = Column(Integer)
    credit_hour_high = Column(Integer)
    credit_hour_low = Column(Integer)
    # credit_hour_indicator = Column(VARCHAR)
    open_section = Column(Boolean)
    link_identifier = Column(VARCHAR)
    is_section_linked = Column(Boolean)
    # reserved_seat_summary = Column(VARCHAR)
    # section_attributes = Column(VARCHAR)

    # CLS -> In-Person
    # WB1 -> Virtual Meet Times
    instructional_method = Column(VARCHAR)

    # In-Person
    # Virtual Meet Times
    instructional_method_description = Column(VARCHAR)


class TBL_Course_Faculty(Base):
    __tablename__ = "tbl_course_faculty"

    course_id = Column(Integer, ForeignKey("tbl_course.course_id"), primary_key=True)

    faculty_id = Column(Integer, ForeignKey("tbl_faculty.faculty_id"), primary_key=True)


class TBL_Faculty(Base):
    __tablename__ = "tbl_faculty"

    faculty_id = Column(Integer, primary_key=True, autoincrement=True)
    banner_id = Column(LargeBinary, unique=True)
    instructor_name = Column(VARCHAR)
    instructor_email = Column(VARCHAR)
    instructor_rating = Column(Integer)


def get_class_type_from_str(value: str, session: Session):
    # Try to find the class_type_id for the given value
    class_type = session.query(TBL_Class_Type).filter_by(class_type=value).first()

    if class_type is not None:
        return class_type.class_type_id

    new_class_type = TBL_Class_Type(class_type=value)
    session.add(new_class_type)

    session.flush()

    return new_class_type.class_type_id


def add_terms(term_ids: list[int], term_descriptions: list[str]):
    if len(term_ids) != len(term_descriptions):
        raise ValueError("term_ids must be the same length as term_descriptions")

    with Session.begin() as session:
        for term_id, term_description in zip(term_ids, term_descriptions):
            stmt = (
                TBL_Terms.__table__.insert()
                .prefix_with("OR IGNORE")
                .values(term_id=term_id, term_description=term_description)
            )
            session.execute(stmt)

        session.flush()


def add_term(term_id: int, term_description: str):
    with Session.begin() as session:
        stmt = (
            TBL_Terms.__table__.insert()
            .prefix_with("OR IGNORE")
            .values(term_id=term_id, term_description=term_description)
        )
        session.execute(stmt)

        session.flush()


def add_courses(term_ids: list[int], course_codes: list[str], course_descriptions: list[str]):
    ids = []

    with Session.begin() as session:
        for term_id, course_code, course_description in zip(
            term_ids, course_codes, course_descriptions
        ):
            result = (
                session.query(TBL_Course)
                .filter_by(term_id=term_id)
                .filter_by(course_code=course_code)
                .first()
            )

            if not result:
                result = TBL_Course(
                    term_id=term_id,
                    course_code=course_code,
                    course_description=course_description,
                )

                session.add(result)

                session.flush()

            ids.append(result.course_id)

    return ids


def add_course(term_id: int, course_code: str, course_description: str):
    with Session.begin() as session:
        result = (
            session.query(TBL_Course)
            .filter_by(term_id=term_id)
            .filter_by(course_code=course_code)
            .first()
        )

        if not result:
            result = TBL_Course(
                term_id=term_id,
                course_code=course_code,
                course_description=course_description,
            )

            session.add(result)

            session.flush()

        return result.course_code


def add_course_data(course_ids: list[int], datas: list[dict[str]]):
    with Session.begin() as session:
        for course_id, data in zip(course_ids, datas):
            logger.debug(f"Adding: {course_id}'s data to the database")

            # if something goes wrong here it's gonna frick everything up
            class_type_id = get_class_type_from_str(data["scheduleTypeDescription"], session)

            logger.debug(f"class_type_id: {class_type_id}")

            stmt = (
                TBL_Course_Data.__table__.insert()
                .prefix_with("OR IGNORE")
                .values(
                    # course code
                    course_id=course_id,
                    #
                    # i have no idea what this value means
                    id=data["id"],
                    #
                    # crn / course reference number; this should be an int always
                    crn=data["courseReferenceNumber"],
                    #
                    # Biology II
                    course_title=data["courseTitle"],
                    # BIOL
                    subject=data["subject"],
                    # Biology
                    subject_long=data["subjectDescription"],
                    #
                    # 001, 002, 003...; should always be int
                    sequence_number=str(data["sequenceNumber"]),
                    #
                    # TODO: add a table for campus instead of using a string
                    campus_description=data["campusDescription"],
                    #
                    # Lecture, Laborator, Tutorial
                    class_type=class_type_id,
                    #
                    credit_hours=data["creditHours"],
                    maximum_enrollment=data["maximumEnrollment"],
                    enrollment=data["enrollment"],
                    seats_vailable=data["seatsAvailable"],
                    wait_capacity=data["waitCapacity"],
                    wait_count=data["waitCount"],
                    wait_available=data["waitAvailable"],
                    # cross_list=data["crossList"],
                    # cross_list_capacity=data["crossListCapacity"],
                    # cross_list_count=data["crossListCount"],
                    # cross_list_available=data["crossListAvailable"],
                    credit_hour_high=data["creditHourHigh"],
                    credit_hour_low=data["creditHourLow"],
                    # credit_hour_indicator=data["creditHourIndicator"],
                    open_section=data["openSection"],
                    link_identifier=data["linkIdentifier"],
                    is_section_linked=data["isSectionLinked"],
                    # subject_course=data["subjectCourse"],
                    # reserved_seat_summary=data["reservedSeatSummary"],
                    # section_attributes=data["sectionAttributes"],
                    instructional_method=data["instructionalMethod"],
                    instructional_method_description=data["instructionalMethodDescription"],
                )
            )

            session.execute(stmt)

            for faculty in data["faculty"]:
                _ = faculty["displayName"] + (faculty.get("emailAddress", "") or "")
                banner_id = dataUtil.sha224_str(_)

                result = session.query(TBL_Faculty).filter_by(banner_id=banner_id).first()

                if not result:
                    result = TBL_Faculty(
                        banner_id=banner_id,
                        instructor_name=faculty["displayName"],
                        instructor_email=faculty["emailAddress"],
                        instructor_rating=0,
                    )

                    session.add(result)
                    session.flush()

                faculty_id = result.faculty_id

                stmt = (
                    TBL_Course_Faculty.__table__.insert()
                    .prefix_with("OR IGNORE")
                    .values(course_id=course_id, faculty_id=faculty_id)
                )

                result = session.execute(stmt)

        session.flush()
