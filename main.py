#Letizia Rosa Laghi

import os
from dotenv import load_dotenv
from sqlmodel import Field, Session, create_engine, select, Relationship, SQLModel
from typing import Optional, List, Annotated
from datetime import date
from fastapi import FastAPI, Depends, Query, HTTPException

#Conexion con la base de datos
load_dotenv()
db_username=os.getenv('USER_DB')
db_password=os.getenv('PASSWORD_DB')
db_host=os.getenv('HOST_DB')
db_name=os.getenv('NAME_DB')

url_connection = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:3306/{db_name}"
engine = create_engine(url_connection)

#Control de sesiones
def get_session():
    with Session(engine) as session:
        yield session

session_dep = Annotated[Session, Depends(get_session)]

#Modelos
class Clientes(SQLModel, table=True):
    __tablename__ = "Clientes"

    cedula: str = Field(primary_key=True, max_length=13)
    nombre: str = Field(max_length=30)
    apellido: str = Field(max_length=30)
    sexo: str = Field(max_length=1)
    telefono: str = Field(max_length=10)
    correo: str = Field(max_length=50)
    
    # Definicion de relacion uno a muchos
    mascotas: List["Mascotas"] = Relationship(back_populates="cliente")
    consultas: List["Consultas"] = Relationship(back_populates="cliente")

class Doctores(SQLModel, table=True):
    __tablename__ = "Doctores"

    cedula: str = Field(primary_key=True, max_length=13)
    nombre: str = Field(max_length=30)
    apellido: str = Field(max_length=30)
    sexo: str = Field(max_length=1)
    telefono: str = Field(max_length=10)
    correo: str = Field(max_length=50)
    
    # Definicion de relacion uno a muchos
    consultas: List["Consultas"] = Relationship(back_populates="doctor")

class Mascotas(SQLModel, table=True):
    __tablename__ = "Mascotas"

    mascotaId: Optional[int] = Field(default=None, primary_key=True) # AI PK
    cedulaCliente: str = Field(foreign_key="Clientes.cedula", max_length=13)
    nombre: str = Field(max_length=30)
    especie: str = Field(max_length=30)
    raza: str = Field(max_length=30)
    sexo: str = Field(max_length=1)
    anioNacimiento: int
    
    # Definicion de relacion muchos a uno con el cliente y uno a muchos con las consultas
    cliente: "Clientes" = Relationship(back_populates="mascotas")
    consultas: List["Consultas"] = Relationship(back_populates="mascota")

class Consultas(SQLModel, table=True):
    __tablename__ = "Consultas"

    consultaID: Optional[int] = Field(default=None, primary_key=True)
    mascotaID: Optional[int] = Field(default=None, foreign_key="Mascotas.mascotaId")
    cedulaCliente: str = Field(foreign_key="Clientes.cedula", max_length=13)
    cedulaDoctor: str = Field(foreign_key="Doctores.cedula", max_length=13)
    fechaConsulta: date
    precioConsulta: float
    
    # Relacion muchos a uno con mascotas, clientes y doctores
    mascota: "Mascotas" = Relationship(back_populates="consultas")
    cliente: "Clientes" = Relationship(back_populates="consultas")
    doctor: "Doctores" = Relationship(back_populates="consultas")
    
class MascotasCreate(SQLModel):
    cedulaCliente: str
    nombre: str
    especie: str
    raza: str
    sexo: str
    anioNacimiento: int
    
class MascotaRead(MascotasCreate):
    mascotaId: int
    
class MascotaUpdate(MascotasCreate):
    cedulaCliente: str | None = None
    nombre: str | None = None
    especie: str | None = None
    raza: str | None = None
    sexo: str | None = None
    anioNacimiento: int | None = None

app = FastAPI()

@app.get('/')
def root():
    return {'mensaje':'Hola mundo'}

@app.post("/mascotas/", response_model=Mascotas)
def crear_mascota(mascota: MascotasCreate, session: session_dep):
    db_mascota = Mascotas.model_validate(mascota)
    session.add(db_mascota)
    session.commit()
    session.refresh(db_mascota)
    return db_mascota

@app.get("/mascotas/", response_model=List[Mascotas])
def consultar_mascotas(
    session: session_dep,
    offset: int=0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    mascotas = session.exec(select(Mascotas).offset(offset).limit(limit)).all()
    return mascotas

@app.get("/mascotas/{mascota_id}", response_model=Mascotas)
def consultar_mascota(mascota_id: int, session: session_dep):
    mascota = session.get(Mascotas, mascota_id)
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return mascota

@app.patch("/mascotas/{mascota_id}", response_model=Mascotas)
def actualizar_mascota(mascota_id: int, mascota: MascotaUpdate, session: session_dep):
    db_mascota = session.get(Mascotas, mascota_id)
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    datos_mascota = mascota.model_dump(exclude_unset=True)
    db_mascota.sqlmodel_update(datos_mascota)
    session.add(db_mascota)
    session.commit()
    session.refresh(db_mascota)
    return db_mascota

@app.delete("/mascotas/{mascota_id}")
def eliminar_mascota(mascota_id: int, session: session_dep):
    mascota = session.get(Mascotas, mascota_id)
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    session.delete(mascota)
    session.commit()
    return {"Ok":"True"}
