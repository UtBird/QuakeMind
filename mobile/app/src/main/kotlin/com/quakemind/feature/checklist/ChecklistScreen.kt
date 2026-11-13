package com.quakemind.feature.checklist

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.selection.toggleable
import androidx.compose.ui.semantics.Role
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quakemind.core.designsystem.*
import com.quakemind.core.model.ChecklistItem

import androidx.compose.foundation.lazy.rememberLazyListState

@Composable
fun ChecklistScreen(
    items: List<ChecklistItem>,
    onToggle: (String) -> Unit,
    onBack: () -> Unit,
) {
    val listState = rememberLazyListState()
    val completedCount = remember(items) { items.count { it.isChecked } }
    val progress = remember(items, completedCount) {
        if (items.isNotEmpty()) completedCount.toFloat() / items.size else 0f
    }
    val groupedCategories = remember(items) { items.groupBy { it.category } }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding()
    ) {
        // Header
        ScreenHeader(title = "Afet çantası", onBack = onBack, subtitle = "İlk 72 saat için hazırlık listesi")

        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .testTag("checklist_lazy_column"),
            state = listState,
            contentPadding = PaddingValues(start = 18.dp, end = 18.dp, top = 6.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {

            // Progress Hero Card (#800E13 Progress)
            item(key = "checklist_progress_hero", contentType = "hero") {
                QuakeCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text("Hazırlık Durumu", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Zinc950)
                        StatusBadge(
                            text = "$completedCount / ${items.size} Tamamlandı",
                            backgroundColor = if (progress >= 1f) AfetGreenMuted else AfetAccentMuted,
                            textColor = if (progress >= 1f) AfetGreen else AfetAccent,
                            borderColor = if (progress >= 1f) AfetGreenBorder else AfetAccentBorder,
                        )
                    }

                    Spacer(Modifier.height(10.dp))

                    LinearProgressIndicator(
                        progress = { progress },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(6.dp)
                            .clip(CircleShape),
                        color = AfetAccent,
                        trackColor = Zinc100,
                    )

                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = if (progress >= 1f) "Listedeki tüm öğeleri işaretlediniz. Çantanızın gerçek içeriğini ayrıca kontrol edin."
                        else "Bu liste bir hazırlık şablonudur. İşaretler yalnızca kullanıcı beyanıdır; fiziksel malzemeleri ayrıca kontrol edin.",
                        fontSize = 12.sp,
                        color = Zinc500,
                    )
                }
            }

            // Checklist Items Grouped by Category
            groupedCategories.forEach { (category, catItems) ->
                item(key = "checklist_category_$category", contentType = "category_header") {
                    Text(
                        text = category,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 12.sp,
                        color = Zinc500,
                        letterSpacing = 1.sp,
                    )
                }

                items(
                    items = catItems,
                    key = { it.id },
                    contentType = { "checklist_item" },
                ) { item ->
                    ChecklistItemCard(
                        item = item,
                        onToggle = onToggle,
                    )
                }
            }
        }
    }
}

@Composable
private fun ChecklistItemCard(
    item: ChecklistItem,
    onToggle: (String) -> Unit,
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .testTag("checklist_item_${item.id}")
            .toggleable(value = item.isChecked, role = Role.Checkbox, onValueChange = { onToggle(item.id) }),
        shape = Shape8dp,
        color = if (item.isChecked) Zinc50 else MaterialTheme.colorScheme.surface,
        border = BorderZinc200,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Surface(
                modifier = Modifier.size(22.dp),
                shape = Shape5dp,
                color = if (item.isChecked) AfetAccent else MaterialTheme.colorScheme.surface,
                border = if (item.isChecked) BorderStroke(1.5.dp, AfetAccent) else BorderZinc400_1_5,
            ) {
                if (item.isChecked) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Outlined.Check, contentDescription = null, tint = MaterialTheme.colorScheme.onPrimary, modifier = Modifier.size(14.dp))
                    }
                }
            }

            Column(Modifier.weight(1f)) {
                Text(
                    text = item.title,
                    fontSize = 14.sp,
                    fontWeight = if (item.isChecked) FontWeight.Medium else FontWeight.SemiBold,
                    color = if (item.isChecked) Zinc500 else Zinc950,
                    textDecoration = if (item.isChecked) TextDecoration.LineThrough else TextDecoration.None,
                )
                Text(
                    text = if (item.isCrucial) "Öncelikli Hayati Malzeme" else "Destek Malzemesi",
                    fontSize = 12.sp,
                    color = if (item.isCrucial) AfetAccent else Zinc400,
                )
            }
        }
    }
}
