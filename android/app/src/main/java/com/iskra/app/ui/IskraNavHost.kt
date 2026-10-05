package com.iskra.app.ui

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.iskra.app.ui.screens.ChatListScreen
import com.iskra.app.ui.screens.ChatScreen
import com.iskra.app.ui.screens.ProjectsScreen

object Routes {
    const val CHAT_LIST = "chat_list"
    const val CHAT = "chat/{chatId}"
    const val PROJECTS = "projects"
    fun chat(chatId: Long) = "chat/$chatId"
}

@Composable
fun IskraNavHost() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Routes.CHAT_LIST
    ) {
        composable(Routes.CHAT_LIST) {
            ChatListScreen(
                onOpenChat = { chatId ->
                    navController.navigate(Routes.chat(chatId))
                },
                onOpenProjects = {
                    navController.navigate(Routes.PROJECTS)
                }
            )
        }
        composable(
            route = Routes.CHAT,
            arguments = listOf(navArgument("chatId") { type = NavType.LongType })
        ) { backStackEntry ->
            val chatId = backStackEntry.arguments?.getLong("chatId") ?: return@composable
            ChatScreen(
                chatId = chatId,
                onBack = { navController.popBackStack() }
            )
        }
        composable(Routes.PROJECTS) {
            ProjectsScreen(onBack = { navController.popBackStack() })
        }
    }
}
