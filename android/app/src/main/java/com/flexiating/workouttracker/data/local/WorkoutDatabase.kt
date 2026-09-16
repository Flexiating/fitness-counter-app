package com.flexiating.workouttracker.data.local

import android.content.Context
import androidx.room.*
import androidx.room.migration.Migration
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Entity(tableName = "workout_sessions")
data class WorkoutSessionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val exercise: String,
    val dateEpochMs: Long,
    val reps: Int,
    val durationMs: Long,
    val averageFormScore: Float,
    val averageFps: Float,
    val endEpochMs: Long = dateEpochMs + durationMs,
    val averageTrackingConfidence: Float = 0f,
    val targetReached: Boolean = false
)

@Dao
interface WorkoutDao {
    @Query("SELECT * FROM workout_sessions WHERE exercise IN ('PUSH_UP', 'CRUNCH') ORDER BY dateEpochMs DESC")
    fun observeAll(): Flow<List<WorkoutSessionEntity>>

    @Query("SELECT * FROM workout_sessions WHERE id = :id")
    fun observe(id: Long): Flow<WorkoutSessionEntity?>

    @Insert suspend fun insert(session: WorkoutSessionEntity)
    @Query("DELETE FROM workout_sessions WHERE id = :id") suspend fun delete(id: Long)
    @Query("DELETE FROM workout_sessions") suspend fun clear()
}

@Database(entities = [WorkoutSessionEntity::class], version = 2, exportSchema = true)
abstract class WorkoutDatabase : RoomDatabase() { abstract fun workoutDao(): WorkoutDao }

@Singleton
class WorkoutRepository @Inject constructor(@ApplicationContext context: Context) {
    private val database = Room.databaseBuilder(context, WorkoutDatabase::class.java, "workout-history.db")
        .addMigrations(object : Migration(1, 2) {
            override fun migrate(db: androidx.sqlite.db.SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE workout_sessions ADD COLUMN endEpochMs INTEGER NOT NULL DEFAULT 0")
                db.execSQL("UPDATE workout_sessions SET endEpochMs = dateEpochMs + durationMs WHERE endEpochMs = 0")
                db.execSQL("ALTER TABLE workout_sessions ADD COLUMN averageTrackingConfidence REAL NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE workout_sessions ADD COLUMN targetReached INTEGER NOT NULL DEFAULT 0")
                db.execSQL("DELETE FROM workout_sessions WHERE exercise NOT IN ('PUSH_UP', 'CRUNCH')")
            }
        })
        .build()
    private val dao = database.workoutDao()
    val sessions: Flow<List<WorkoutSessionEntity>> = dao.observeAll()
    suspend fun save(session: WorkoutSessionEntity) = dao.insert(session)
    fun session(id: Long): Flow<WorkoutSessionEntity?> = dao.observe(id)
    suspend fun delete(id: Long) = dao.delete(id)
    suspend fun clear() = dao.clear()
}
