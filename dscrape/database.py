from sqlalchemy import Date, Float, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy import event
from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    TIMESTAMP,
    LargeBinary,
    BigInteger,
    BINARY,
    VARCHAR,
    ForeignKey,
)
from sqlalchemy import UniqueConstraint
import os
import datetime

from . import dataUtil
from . import logger


class Scrape:

    Scrape_Time = datetime.datetime.now(datetime.timezone.utc)
    Scrape_id   = -1

Engine = None
Session: sessionmaker = None
Base = declarative_base()


def init_database(
    use_mysql=False,
    database_host="localhost",
    database_port=3306,
    database_name="hibernate_db",
    database_user="test",
    database_pass="root",
    database_directory="./",
):
    global Engine, Session, Base

    if Engine is not None:
        raise Exception("Database engine already initialized")

    os.makedirs(database_directory, exist_ok=True)

    db_path = os.path.join(database_directory, database_name)
    DB_URL = f"sqlite:///{db_path}.sqlite"
    if use_mysql:
        DB_URL = f"mysql+mysqlconnector://{database_user}:{database_pass}@{database_host}:{database_port}/{database_name}"
    Engine = create_engine(DB_URL, echo=False)

    def _fk_pragma_on_connect(dbapi_con, con_record):
        if use_mysql:
            return
        dbapi_con.execute("pragma foreign_keys=ON")

    event.listen(Engine, "connect", _fk_pragma_on_connect)

    Session = sessionmaker(bind=Engine)
    Base.metadata.bind = Engine
    Base.metadata.create_all(Engine)


class TBL_Scrape_History(Base):
    __tablename__ = "tbl_scrape_history"

    scrape_id = Column(Integer, primary_key=True, autoincrement=True)
    scrape_time = Column(TIMESTAMP)
    has_been_indexed = Column(Boolean)


class TBL_Term(Base):
    __tablename__ = "tbl_term"

    term_id = Column(Integer, primary_key=True)
    term_description = Column(VARCHAR(128))


class TBL_Course(Base):
    __tablename__ = "tbl_course"

    course_id = Column(Integer, primary_key=True, autoincrement=True)
    term_id = Column(Integer, ForeignKey("tbl_term.term_id"))
    course_code = Column(VARCHAR(32))
    course_description = Column(VARCHAR(128))

    __table_args__ = (
        UniqueConstraint("term_id", "course_code", name="_term_id_course_code_constraint"),
    )


class TBL_Class_Type(Base):
    __tablename__ = "tbl_classtype"

    class_type_id = Column(Integer, primary_key=True, autoincrement=True)
    class_type = Column(VARCHAR(128))


class TBL_Course_Data(Base):
    __tablename__ = "tbl_course_data"

    course_data_id = Column(Integer, autoincrement=True, primary_key=True)

    course_id = Column(Integer, ForeignKey("tbl_course.course_id"))

    scrape_id = Column(Integer, ForeignKey("tbl_scrape_history.scrape_id"))

    # course reference number / crn
    crn = Column(VARCHAR(32))
    # i'm not really sure what this actually is
    id = Column(Integer)

    # Biology II
    course_title = Column(VARCHAR(128))
    # BIOL
    subject = Column(VARCHAR(128))
    # Biology
    subject_long = Column(VARCHAR(128))

    # 001 / 002 / 003...; conerting to int so will need to pad 0 later if needed
    sequence_number = Column(VARCHAR(128))

    # which campus -> 'OT-North Oshawa'
    campus_description = Column(VARCHAR(128))

    # lab, lecture, tutorial
    class_type_id = Column(Integer, ForeignKey("tbl_classtype.class_type_id"))

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
    link_identifier = Column(VARCHAR(128))
    is_section_linked = Column(Boolean)
    # reserved_seat_summary = Column(VARCHAR)
    # section_attributes = Column(VARCHAR)

    # CLS -> In-Person
    # WB1 -> Virtual Meet Times
    instructional_method = Column(VARCHAR(128))

    # In-Person
    # Virtual Meet Times
    instructional_method_description = Column(VARCHAR(128))

    __table_args__ = (UniqueConstraint("course_id", "crn", name="_course_id_crn_constraint"),)


class TBL_Course_Faculty(Base):
    __tablename__ = "tbl_course_faculty"

    course_data_id = Column(Integer, ForeignKey("tbl_course_data.course_data_id"), primary_key=True)

    faculty_id = Column(Integer, ForeignKey("tbl_faculty.faculty_id"), primary_key=True)


class TBL_Faculty(Base):
    __tablename__ = "tbl_faculty"

    faculty_id = Column(Integer, primary_key=True, autoincrement=True)
    banner_id = Column(BINARY(length=32), unique=True, nullable=False)
    scrape_id = Column(Integer, ForeignKey("tbl_scrape_history.scrape_id"))
    instructor_name = Column(VARCHAR(128))
    instructor_email = Column(VARCHAR(128))
    instructor_rating = Column(Integer)



class TBL_Meeting(Base):
    __tablename__ = "tbl_meeting"

    meeting_id = Column(Integer, autoincrement=True, primary_key=True)

    meeting_hash = Column(BINARY(length=32), unique=True, nullable=False)

    course_data_id = Column(Integer, ForeignKey("tbl_course_data.course_data_id"))

    term_id = Column(Integer, ForeignKey("tbl_term.term_id"))
    

    crn = Column(VARCHAR(32))

    building = Column(VARCHAR(128))
    building_description = Column(VARCHAR(128))

    campus = Column(VARCHAR(128))
    campus_description = Column(VARCHAR(128))

    meeting_type = Column(VARCHAR(128))
    meeting_type_description = Column(VARCHAR(128))

    start_date = Column(Date)
    end_date = Column(Date)

    begin_time = Column(VARCHAR(128))
    end_time = Column(VARCHAR(128))

    days_of_week = Column(Integer)

    room = Column(VARCHAR(128))

    category = Column(VARCHAR(128))
    credit_hour_session = Column(Float)
    hours_week = Column(Float)
    meeting_schedule_type = Column(VARCHAR(128))
    
    



def get_current_scrape():

    if Scrape.Scrape_id != -1:
        return Scrape.Scrape_id

    logger.info("Inserting new scrape")
    with Session.begin() as session:

        result = session.query(TBL_Scrape_History).filter_by(scrape_time=Scrape.Scrape_Time).first()

        if not result:

            result = TBL_Scrape_History(
                scrape_time=Scrape.Scrape_Time,
                has_been_indexed=False
            ) 

            session.add(result)
            session.flush()

        Scrape.Scrape_id = result.scrape_id

        logger.info(f"Current Scrape ID: {Scrape.Scrape_id}")

        return result.scrape_id



def get_class_type_from_str(value: str, session):
    # Try to find the class_type_id for the given value
    class_type_id = session.query(TBL_Class_Type).filter_by(class_type=value).first()

    if class_type_id is not None:
        return class_type_id.class_type_id

    new_class_type = TBL_Class_Type(class_type=value)
    session.add(new_class_type)

    session.flush()

    return new_class_type.class_type_id


def add_terms(term_ids: list[int], term_descriptions: list[str]):
    if len(term_ids) != len(term_descriptions):
        raise ValueError("term_ids must be the same length as term_descriptions")

    with Session.begin() as session:
        for term_id, term_description in zip(term_ids, term_descriptions):
            term_id = int(term_id)

            result = session.query(TBL_Term).filter_by(term_id=term_id).first()

            if not result:
                result = TBL_Term(
                    term_id=term_id,
                    term_description=term_description,
                )

                session.add(result)

        session.flush()


def add_term_no_transaction(term_id: int, term_description: str, session: sessionmaker):
    result = session.query(TBL_Term).filter_by(term_id=term_id).first()

    if not result:
        result = TBL_Term(
            term_id=int(term_id),
            term_description=term_description,
        )

        session.add(result)

        session.flush()


def add_term(term_id: int, term_description: str):
    with Session.begin() as session:
        add_term_no_transaction(term_id, term_description, session)


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

            result = (
                session.query(TBL_Course_Data)
                .filter_by(course_id=course_id)
                .filter_by(crn=data["courseReferenceNumber"])
                .first()
            )

            if result:
                logger.info(
                    f"CourseData with course_id={course_id} and crn={data['courseReferenceNumber']}"
                )
            else:
                result = TBL_Course_Data(
                    # course code
                    course_id=course_id,
                        scrape_id = get_current_scrape(),
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
                    # TODO: add a table for campus instead of using a VARCHAR
                    campus_description=data["campusDescription"],
                    #
                    # Lecture, Laborator, Tutorial
                    class_type_id=class_type_id,
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
                session.add(result)
                session.flush()

            course_data_id = result.course_data_id

            for faculty in data["faculty"]:
                _ = faculty["displayName"] + (faculty.get("emailAddress", "") or "")
                banner_id = dataUtil.sha256_of_str(_)
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

                result = (
                    session.query(TBL_Course_Faculty)
                    .filter_by(course_data_id=course_data_id)
                    .filter_by(faculty_id=faculty_id)
                    .first()
                )

                if not result:
                    result = TBL_Course_Faculty(
                        course_data_id=course_data_id, faculty_id=faculty_id
                    )

                    session.add(result)

            # session.flush()

            for meeting in data["meetingsFaculty"]:
                useful_data = meeting["meetingTime"]

                crn = useful_data["courseReferenceNumber"]
                term_id = dataUtil.parse_int(useful_data["term"])
                if term_id == -1:
                    logger.warning(
                        f"Got bad term_id of {useful_data['term']} course_id={course_id} for meeting {meeting}"
                    )
                    continue

                add_term_no_transaction(term_id, "UNKNOWN AT TIME OF ADDING", session)

                to_insert = TBL_Meeting(
                    meeting_hash=b"",
                    course_data_id=course_data_id,
                    crn=crn,
                    term_id=term_id,
                    building=useful_data["building"],
                    building_description=useful_data["buildingDescription"],
                    campus=useful_data["campus"],
                    campus_description=useful_data["campusDescription"],
                    meeting_type=useful_data["meetingType"],
                    meeting_type_description=useful_data["meetingTypeDescription"],
                    start_date=dataUtil.parse_date(useful_data["startDate"]),
                    end_date=dataUtil.parse_date(useful_data["endDate"]),
                    begin_time=useful_data["beginTime"],
                    end_time=useful_data["endTime"],
                    days_of_week=dataUtil.get_weekdays_int(useful_data),
                    room=useful_data["room"],
                    category=useful_data["category"],
                    credit_hour_session=useful_data["creditHourSession"],
                    hours_week=useful_data["hoursWeek"],
                    meeting_schedule_type=useful_data["meetingScheduleType"],
                )

                # we need to make our own unique identifier for the meeting
                # so this is it, just all the data i figured was important
                meeting_hash = dataUtil.sha256_of_str(
                    f"{crn}{term_id}{to_insert.building}{to_insert.campus}{to_insert.meeting_type}"
                    f"{to_insert.start_date}{to_insert.end_date}{to_insert.begin_time}{to_insert.end_time}"
                    f"{to_insert.days_of_week}{to_insert.room}"
                )

                to_insert.meeting_hash = meeting_hash

                result = session.query(TBL_Meeting).filter_by(meeting_hash=meeting_hash).first()

                if not result:
                    session.add(to_insert)

        session.flush()
