package com.flexiating.workouttracker.data.local

import android.content.Context
import androidx.room.*
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
    val averageFps: Float
)

@Dao
interface WorkoutDao {
    @Query("SELECT * FROM workout_sessions ORDER BY dateEpochMs DESC")
    fun observeAll(): Flow<List<WorkoutSessionEntity>>

    @Insert suspend fun insert(session: WorkoutSessionEntity)
    @Query("DELETE FROM workout_sessions") suspend fun clear()
}

@Database(entities = [WorkoutSessionEntity::class], version = 1, exportSchema = true)
abstract class WorkoutDatabase : RoomDatabase() { abstract fun workoutDao(): WorkoutDao }

@Singleton
class WorkoutRepository @Inject constructor(@ApplicationContext context: Context) {
    private val database = Room.databaseBuilder(context, WorkoutDatabase::class.java, "workout-history.db")
        .fallbackToDestructiveMigration(false)
        .build()
    private val dao = database.workoutDao()
    val sessions: Flow<List<WorkoutSessionEntity>> = dao.observeAll()
    suspend fun save(session: WorkoutSessionEntity) = dao.insert(session)
    suspend fun clear() = dao.clear()
}

